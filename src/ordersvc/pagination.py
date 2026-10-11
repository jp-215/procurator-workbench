"""Cursor pagination — see SPEC.md AC-16..AC-19."""
from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from typing import Any

from ordersvc.errors import ValidationError


@dataclass
class Page:
    items: list[Any] = field(default_factory=list)
    next_cursor: str | None = None


def _get_field(item: Any, name: str) -> Any:
    """Extract a field from either a mapping or an object with attributes."""
    if isinstance(item, dict):
        if name not in item:
            raise ValidationError(f"item missing required field {name!r}")
        return item[name]
    if hasattr(item, name):
        return getattr(item, name)
    raise ValidationError(f"item missing required field {name!r}")


def _sort_key(item: Any) -> tuple[Any, Any]:
    created_at = _get_field(item, "created_at")
    item_id = _get_field(item, "id")
    return (created_at, item_id)


def _encode_cursor(created_at: Any, item_id: Any) -> str:
    payload = json.dumps([created_at, item_id])
    token_bytes = payload.encode("utf-8")
    return base64.urlsafe_b64encode(token_bytes).decode("ascii")


def _decode_cursor(cursor: str) -> tuple[Any, Any]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii"))
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise ValidationError(f"invalid cursor: {cursor!r}") from exc

    if not isinstance(payload, list) or len(payload) != 2:
        raise ValidationError(f"invalid cursor: {cursor!r}")

    created_at, item_id = payload
    return (created_at, item_id)


def paginate(items: list[Any], limit: int, cursor: str | None = None) -> Page:
    if limit <= 0:
        raise ValidationError("limit must be a positive integer")

    sorted_items = sorted(items, key=_sort_key)

    start_index = 0
    if cursor is not None:
        cursor_key = _decode_cursor(cursor)
        # find the first index whose sort key is strictly greater than cursor_key
        start_index = len(sorted_items)
        for idx, item in enumerate(sorted_items):
            if _sort_key(item) > cursor_key:
                start_index = idx
                break

    slice_items = sorted_items[start_index:start_index + limit]
    end_index = start_index + len(slice_items)

    next_cursor: str | None = None
    if end_index < len(sorted_items) and slice_items:
        last_created_at, last_id = _sort_key(slice_items[-1])
        next_cursor = _encode_cursor(last_created_at, last_id)

    return Page(items=slice_items, next_cursor=next_cursor)