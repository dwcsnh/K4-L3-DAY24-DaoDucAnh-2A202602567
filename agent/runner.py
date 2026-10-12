"""BƯỚC 3c — trifecta split + egress allowlist (13').

Tách 1 yêu cầu người dùng thành ít nhất 2 run riêng biệt:
    Run A: gọi search_docs (untrusted content).
           KHÔNG gọi read_customer. KHÔNG gọi http_post.
    Run B: gọi read_customer (private data).
           CHỈ nhận input là TYPED, ĐÃ SANITIZE từ Run A — ví dụ
           list[int] ticket id trích từ TÊN FILE.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from agent import ledger, pii, policy, tools
from agent.policy import PolicyContext

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CUSTOMERS_FILE = DATA_DIR / "customers.json"
DEFAULT_LEDGER_PATH = REPORTS_DIR / "ledger.jsonl"


class RunnerScaffoldPending(NotImplementedError):
    """Only the original 3c stub uses this to enable the CP1/CP2 baseline."""


def handle(message: str, llm, log_dir: Path | None = None,
           principal_id: str = "support_l1") -> str:
    """Xử lý yêu cầu người dùng với cơ chế phân tách Run A và Run B, kiểm soát chính sách và ghi ledger."""
    if log_dir is None:
        ledger_path = DEFAULT_LEDGER_PATH
    else:
        p = Path(log_dir)
        ledger_path = p if (p.is_file() or str(p).endswith(".jsonl")) else p / "ledger.jsonl"

    expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()

    # ==================== RUN A: UNTRUSTED INGESTION ====================
    # Run A chỉ thực hiện tìm kiếm tài liệu trên corpus, không chạm private store và egress.
    search_ctx = PolicyContext(
        data_classification="internal",
        request_purpose="summarize-tickets",
        agent_owner="lab24-agent/run-a",
        delegation_depth=0,
        egress_enabled=False,
        principal_id=principal_id,
        requested_tool="search_docs",
        agent_scopes=("search_docs", "read_customer"),
        parent_scopes=(),
        expires_at=expires_at,
    )
    allow_search, search_reason = policy.check(search_ctx)
    ledger.append({
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent_id": "lab24-agent",
        "run_id": "run-a",
        "tool": "search_docs",
        "args_hash": hashlib.sha256(message.encode("utf-8")).hexdigest()[:16],
        "classification": "internal",
        "decision": "allow" if allow_search else "deny",
        "reason": search_reason,
        "on_behalf_of": principal_id,
        "expires_at": expires_at,
    }, ledger_path)

    if not allow_search:
        return "Yêu cầu bị từ chối bởi chính sách bảo mật."

    docs = tools.search_docs(message)

    # Trích xuất ticket_id dạng số từ tên file, tuyệt đối không lấy từ free text
    matched_ticket_ids: set[int] = set()
    for doc in docs:
        doc_name = doc.get("id", "")
        m = re.search(r"ticket-(\d+)", doc_name)
        if m:
            matched_ticket_ids.add(int(m.group(1)))

    combined_text = "\n\n".join(d.get("text", "") for d in docs)
    injected = llm.find_injection(combined_text)

    # ==================== RUN B: PRIVATE DATA ACCESS ====================
    # Run B chỉ nhận danh sách ticket_id dạng số và tra cứu khách hàng qua related_tickets đáng tin cậy.
    customers_data = json.loads(CUSTOMERS_FILE.read_text(encoding="utf-8")) if CUSTOMERS_FILE.exists() else []

    # Tìm khách hàng liên quan dựa trên related_tickets
    target_customers = []
    for cust in customers_data:
        cust_tickets = cust.get("related_tickets", [])
        if any(t in matched_ticket_ids for t in cust_tickets):
            target_customers.append(cust["customer_id"])

    collected_records = []
    for customer_id in sorted(set(target_customers)):
        read_ctx = PolicyContext(
            data_classification="restricted",
            request_purpose="support-reply",
            agent_owner="lab24-agent/run-b",
            delegation_depth=0,
            egress_enabled=False,
            principal_id=principal_id,
            requested_tool="read_customer",
            agent_scopes=("search_docs", "read_customer"),
            parent_scopes=(),
            expires_at=expires_at,
        )
        allow_read, read_reason = policy.check(read_ctx)
        ledger.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "agent_id": "lab24-agent",
            "run_id": "run-b",
            "tool": "read_customer",
            "args_hash": hashlib.sha256(customer_id.encode("utf-8")).hexdigest()[:16],
            "classification": "restricted",
            "decision": "allow" if allow_read else "deny",
            "reason": read_reason,
            "on_behalf_of": principal_id,
            "expires_at": expires_at,
        }, ledger_path)

        if allow_read:
            try:
                record = tools.read_customer(customer_id)
                collected_records.append(record)
            except tools.ToolError:
                continue

    # ==================== EGRESS POLICY CHECK ====================
    # Nếu phát hiện chỉ thị yêu cầu gửi dữ liệu ra ngoài, kiểm tra chính sách và chặn egress
    if injected is not None:
        post_ctx = PolicyContext(
            data_classification="restricted",
            request_purpose="support-reply",
            agent_owner="lab24-agent/run-b",
            delegation_depth=0,
            egress_enabled=True,
            principal_id=principal_id,
            requested_tool="http_post",
            agent_scopes=("search_docs", "read_customer"),
            parent_scopes=(),
            expires_at=expires_at,
        )
        allow_post, post_reason = policy.check(post_ctx)
        ledger.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "agent_id": "lab24-agent",
            "run_id": "run-b",
            "tool": "http_post",
            "args_hash": hashlib.sha256(injected.target_url.encode("utf-8")).hexdigest()[:16],
            "classification": "restricted",
            "decision": "allow" if allow_post else "deny",
            "reason": post_reason,
            "on_behalf_of": principal_id,
            "expires_at": expires_at,
        }, ledger_path)

        if allow_post:
            tools.http_post(injected.target_url, {"records": collected_records})

    # Áp dụng PII redaction trước khi trả về tổng hợp
    redacted_docs = []
    for d in docs:
        redacted_docs.append({
            "id": d.get("id", ""),
            "text": pii.redact(d.get("text", "")),
        })

    return llm.summarize(redacted_docs)
