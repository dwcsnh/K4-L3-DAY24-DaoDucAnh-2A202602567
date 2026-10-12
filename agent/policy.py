"""BƯỚC 3b — PEP (Policy Enforcement Point) tại tool call.

Cổng chặn TRƯỚC KHI tool thật sự execute. Đọc CHECKPOINTS.md (§3b).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PRINCIPALS_PATH = BASE_DIR / "data" / "principals.json"


@dataclass(frozen=True)
class PolicyContext:
    data_classification: str
    request_purpose: str
    agent_owner: str
    delegation_depth: int
    egress_enabled: bool
    principal_id: str = ""
    requested_tool: str = ""
    agent_scopes: tuple[str, ...] = ()
    parent_scopes: tuple[str, ...] = ()
    expires_at: str = ""


def _load_principals() -> dict:
    if PRINCIPALS_PATH.exists():
        return json.loads(PRINCIPALS_PATH.read_text(encoding="utf-8"))
    return {}


def check(context: PolicyContext) -> tuple[bool, str]:
    """Kiểm tra chính sách trước khi cho phép tool thực thi."""
    # 1. Rule tối thiểu: dữ liệu restricted không bao giờ được egress ra ngoài
    if context.data_classification == "restricted" and context.egress_enabled:
        return False, "Restricted data classification cannot be egressed"

    # 2. Kiểm tra công cụ egress khi egress bị tắt
    if context.requested_tool == "http_post":
        if not context.egress_enabled:
            return False, "Network egress is disabled for this context"
        if context.data_classification == "restricted":
            return False, "Restricted data cannot be sent via http_post"

    # 3. Kiểm tra hạn sử dụng của phiên làm việc
    if context.expires_at:
        try:
            exp = datetime.fromisoformat(context.expires_at)
            now = datetime.now(timezone.utc)
            if exp <= now:
                return False, f"Session expired at {context.expires_at}"
        except Exception:
            return False, f"Invalid expires_at format: {context.expires_at}"

    # 4. Kiểm tra danh tính principal
    if not context.principal_id:
        return False, "Missing principal identity"

    principals = _load_principals()
    if context.principal_id not in principals:
        return False, f"Unknown principal: {context.principal_id}"

    principal_info = principals[context.principal_id]

    # 5. Kiểm tra mục đích thực hiện
    allowed_purposes = set(principal_info.get("purposes", []))
    if context.request_purpose and context.request_purpose not in allowed_purposes:
        return False, f"Purpose {context.request_purpose} is not permitted for {context.principal_id}"

    # 6. Tính toán quyền hiệu lực theo OBO và delegation
    effective_tools = set(principal_info.get("allowed_tools", []))
    if context.agent_scopes:
        effective_tools &= set(context.agent_scopes)
    if context.delegation_depth > 0:
        effective_tools &= set(context.parent_scopes)

    # 7. Kiểm tra tool được yêu cầu
    if context.requested_tool:
        if context.requested_tool not in effective_tools:
            return False, (
                f"Tool {context.requested_tool} is not permitted for {context.principal_id} "
                f"under current scopes and delegation"
            )

    return True, f"Tool {context.requested_tool or 'action'} authorized for principal {context.principal_id}"
