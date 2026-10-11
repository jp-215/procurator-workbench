"""Cursor pagination — see SPEC.md AC-16..AC-19."""
from __future__ import annotations

import base64
from dataclasses import dataclass, field
from typing import Any

from ordersvc.errors import ValidationError


@dataclass
class Page:
    items: list[Any] = field(default_factory=list)
    next_cursor: str | None = None


_SEP = "|"


def _get_created_at(item: Any) -> float:
    if isinstance(item, dict):
        return item["created_at"]
    return item.created_at


def _get_id(item: Any) -> str:
    if isinstance(item, dict):
        return item["id"]
    return item.id


def _sort_key(item: Any) -> tuple[float, str]:
    return (_get_created_at(item), _get_id(item))


def _encode_cursor(created_at: float, id_: str) -> str:
    raw = f"{created_at!r}{_SEP}{id_}"
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")


def _decode_cursor(cursor: str) -> tuple[float, str]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii")).decode("utf-8")
    except Exception as exc:
        raise ValidationError(f"invalid cursor: {cursor!r}") from exc

    if _SEP not in raw:
        raise ValidationError(f"invalid cursor: {cursor!r}")

    created_at_str, _, id_part = raw.partition(_SEP)
    try:
        created_at = float(created_at_str)
    except ValueError as exc:
        raise ValidationError(f"invalid cursor: {cursor!r}") from exc

    if not id_part:
        raise ValidationError(f"invalid cursor: {cursor!r}")

    return created_at, id_part


def paginate(items: list[Any], limit: int, cursor: str | None = None) -> Page:
    if not isinstance(limit, int) or limit <= 0:
        raise ValidationError("limit must be a positive integer")

    sorted_items = sorted(items, key=_sort_key)

    start_index = 0
    if cursor is not None:
        cursor_key = _decode_cursor(cursor)
        # Find the first index whose sort key is strictly greater than cursor_key.
        start_index = len(sorted_items)
        for i, item in enumerate(sorted_items):
            if _sort_key(item) > cursor_key:
                start_index = i
                break

    page_items = sorted_items[start_index:start_index + limit]

    next_cursor: str | None = None
    end_index = start_index + len(page_items)
    if end_index < len(sorted_items) and page_items:
        last_item = page_items[-1]
        next_cursor = _encode_cursor(_get_created_at(last_item), _get_id(last_item))

    return Page(items=page_items, next_cursor=next_cursor)