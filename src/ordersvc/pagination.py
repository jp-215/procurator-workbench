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
    if isinstance(item, dict):
        return item[name]
    return getattr(item, name)


def _sort_key(item: Any) -> tuple[Any, Any]:
    return (_get_field(item, "created_at"), _get_field(item, "id"))


def _encode_cursor(key: tuple[Any, Any]) -> str:
    payload = json.dumps(list(key))
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")


def _decode_cursor(cursor: str | None) -> tuple[Any, Any] | None:
    if not cursor:
        return None
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii")).decode("utf-8")
        data = json.loads(raw)
        if not isinstance(data, list) or len(data) != 2:
            return None
        return (data[0], data[1])
    except Exception:
        # Defensive: any malformed cursor is treated as "start from beginning".
        return None


def paginate(items: list[Any], limit: int, cursor: str | None = None) -> Page:
    sorted_items = sorted(items, key=_sort_key)

    if limit is None or limit <= 0:
        return Page(items=[], next_cursor=None)

    start_key = _decode_cursor(cursor)

    if start_key is None:
        start_idx = 0
    else:
        start_idx = len(sorted_items)
        for i, it in enumerate(sorted_items):
            try:
                if _sort_key(it) > start_key:
                    start_idx = i
                    break
            except TypeError:
                # Incomparable keys (e.g. mixed types) — skip defensively,
                # treat as not-yet-reached.
                continue

    page_items = sorted_items[start_idx:start_idx + limit]
    next_idx = start_idx + len(page_items)

    if page_items and next_idx < len(sorted_items):
        next_cursor = _encode_cursor(_sort_key(page_items[-1]))
    else:
        next_cursor = None

    return Page(items=page_items, next_cursor=next_cursor)