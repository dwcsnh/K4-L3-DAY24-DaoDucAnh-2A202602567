"""BƯỚC 3a — PII gate TRƯỚC KHI vào context/store (12').

Interface bắt buộc:
    detect(text: str) -> list[dict]
        Mỗi entity: {"type": str, "start": int, "end": int}
        type: "VN_CCCD", "VN_PHONE", "VN_BANK_ACCOUNT", "EMAIL"
    redact(text: str) -> str
        Thay thế entity bằng "[REDACTED_<TYPE>]"
"""
from __future__ import annotations

import re


def detect(text: str) -> list[dict]:
    """Phát hiện PII gồm CCCD, SĐT, STK, email trong văn bản."""
    entities: list[dict] = []

    # 1. Email
    for m in re.finditer(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text):
        entities.append({"type": "EMAIL", "start": m.start(), "end": m.end()})

    # 2. Bank account: đi kèm STK / số tài khoản / TK
    for m in re.finditer(r"(?i)(?:STK|số tài khoản|tài khoản|TK)\s*[:\s]*(\d{8,16})\b", text):
        start = m.start(1)
        end = m.end(1)
        entities.append({"type": "VN_BANK_ACCOUNT", "start": start, "end": end})

    # 3. CCCD: 12 chữ số liên tiếp
    for m in re.finditer(r"\b\d{12}\b", text):
        if not any(e["start"] <= m.start() and m.end() <= e["end"] for e in entities):
            entities.append({"type": "VN_CCCD", "start": m.start(), "end": m.end()})

    # 4. Phone: 10 chữ số bắt đầu bằng 0 hoặc +84
    for m in re.finditer(r"(?:\+84|0)\d{9}\b", text):
        if not any(e["start"] <= m.start() and m.end() <= e["end"] for e in entities):
            entities.append({"type": "VN_PHONE", "start": m.start(), "end": m.end()})

    entities.sort(key=lambda x: x["start"])
    return entities


def redact(text: str) -> str:
    """Thay thế các thực thể PII được phát hiện bằng thẻ [REDACTED_<TYPE>]."""
    entities = detect(text)
    if not entities:
        return text

    # Lọc bỏ các entity trùng lặp/chồng lấn nếu có
    non_overlapping: list[dict] = []
    for ent in sorted(entities, key=lambda x: (x["start"], -x["end"])):
        if not non_overlapping:
            non_overlapping.append(ent)
        else:
            prev = non_overlapping[-1]
            if ent["start"] >= prev["end"]:
                non_overlapping.append(ent)

    # Thay thế ngược từ cuối về đầu để không làm lệch offset
    result = text
    for ent in sorted(non_overlapping, key=lambda x: x["start"], reverse=True):
        tag = f"[REDACTED_{ent['type']}]"
        result = result[:ent["start"]] + tag + result[ent["end"]:]
    return result
