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


def _get_created_at(item: Any) -> Any:
    if isinstance(item, dict):
        return item.get("created_at")
    return getattr(item, "created_at")


def _get_id(item: Any) -> Any:
    if isinstance(item, dict):
        return item.get("id")
    return getattr(item, "id")


def _sort_key(item: Any) -> tuple:
    return (_get_created_at(item), _get_id(item))


def _encode_cursor(created_at: Any, id_: Any) -> str:
    payload = json.dumps([created_at, id_])
    raw = payload.encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def _decode_cursor(cursor: str) -> tuple:
    raw = base64.urlsafe_b64decode(cursor.encode("ascii"))
    data = json.loads(raw.decode("utf-8"))
    return (data[0], data[1])


def paginate(items: list[Any], limit: int, cursor: str | None = None) -> Page:
    sorted_items = sorted(items, key=_sort_key)

    start = 0
    if cursor is not None:
        cursor_key = _decode_cursor(cursor)
        # find first index whose key is strictly greater than cursor_key
        start = len(sorted_items)
        for i, item in enumerate(sorted_items):
            if _sort_key(item) > cursor_key:
                start = i
                break

    slice_items = sorted_items[start:start + limit]

    next_cursor: str | None = None
    if start + limit < len(sorted_items):
        last_item = slice_items[-1]
        next_cursor = _encode_cursor(_get_created_at(last_item), _get_id(last_item))

    return Page(items=slice_items, next_cursor=next_cursor)