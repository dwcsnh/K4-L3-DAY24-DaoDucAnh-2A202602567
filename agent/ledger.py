"""BƯỚC 3d — audit ledger append-only, tamper-evident (10').

JSONL, mỗi tool call một dòng. Đọc CHECKPOINTS.md (§3d).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def append(entry: dict, path: Path) -> dict:
    """Ghi thêm một bản ghi vào ledger với chuỗi hash chống sửa đổi."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    prev_hash = "0" * 64
    if path.exists() and path.stat().st_size > 0:
        lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if lines:
            try:
                last_record = json.loads(lines[-1])
                prev_hash = last_record.get("hash", "0" * 64)
            except Exception:
                prev_hash = "0" * 64

    record = dict(entry)
    record["prev_hash"] = prev_hash

    # Loại bỏ field hash nếu đã tồn tại để tính toán hash
    to_hash = {k: v for k, v in record.items() if k != "hash"}
    canonical = json.dumps(to_hash, sort_keys=True, ensure_ascii=False)
    record_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    record["hash"] = record_hash

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return record


def verify(path: Path) -> bool:
    raise NotImplementedError("BƯỚC 3e: implement ledger verify")

