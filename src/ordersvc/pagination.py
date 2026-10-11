"""Cursor pagination — see SPEC.md AC-16..AC-19."""
from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Page:
    items: list[Any] = field(default_factory=list)
    next_cursor: str | None = None


def _get_field(item: Any, name: str) -> Any:
    """Access a field on either a dict or an object with attributes."""
    if isinstance(item, dict):
        return item[name]
    return getattr(item, name)


def _sort_key(item: Any) -> tuple[Any, Any]:
    return (_get_field(item, "created_at"), _get_field(item, "id"))


def _encode_cursor(key: tuple[Any, Any]) -> str:
    payload = json.dumps(list(key), separators=(",", ":"))
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")


def _decode_cursor(cursor: str) -> tuple[Any, Any]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii"))
        decoded = json.loads(raw.decode("utf-8"))
        if not isinstance(decoded, list) or len(decoded) != 2:
            raise ValueError("malformed cursor payload")
        return (decoded[0], decoded[1])
    except Exception as exc:  # pragma: no cover - defensive
        raise ValueError(f"invalid cursor: {cursor!r}") from exc


def paginate(items: list[Any], limit: int, cursor: str | None = None) -> Page:
    # AC-18: deterministic ordering by (created_at asc, id asc), regardless
    # of input order.
    sorted_items = sorted(items, key=_sort_key)

    start = 0
    if cursor is not None:
        last_key = _decode_cursor(cursor)
        # AC-17: resume strictly after the position encoded by the cursor,
        # with no overlap or gaps.
        start = len(sorted_items)
        for i, it in enumerate(sorted_items):
            if _sort_key(it) > last_key:
                start = i
                break

    if limit < 0:
        limit = 0

    end = start + limit
    page_items = sorted_items[start:end]

    next_cursor = None
    if end < len(sorted_items) and page_items:
        next_cursor = _encode_cursor(_sort_key(page_items[-1]))

    return Page(items=page_items, next_cursor=next_cursor)