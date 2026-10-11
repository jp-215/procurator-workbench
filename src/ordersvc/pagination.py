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


def _sort_key(item: Any) -> tuple[Any, Any]:
    """Extract (created_at, id) from either a dict-like or attribute-based item."""
    if isinstance(item, dict):
        try:
            return (item["created_at"], item["id"])
        except KeyError as exc:
            raise ValidationError(f"item missing required key: {exc}") from exc
    try:
        return (item.created_at, item.id)
    except AttributeError as exc:
        raise ValidationError(f"item missing required attribute: {exc}") from exc


def _encode_cursor(offset: int) -> str:
    raw = f"offset:{offset}".encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def _decode_cursor(cursor: str) -> int:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii")).decode("utf-8")
        prefix, _, value = raw.partition(":")
        if prefix != "offset" or value == "":
            raise ValueError("malformed cursor payload")
        offset = int(value)
    except Exception as exc:
        raise ValidationError("invalid cursor") from exc
    if offset < 0:
        raise ValidationError("invalid cursor")
    return offset


def paginate(items: list[Any], limit: int, cursor: str | None = None) -> Page:
    if not isinstance(limit, int) or limit < 0:
        raise ValidationError("limit must be a non-negative integer")

    sorted_items = sorted(items, key=_sort_key)
    total = len(sorted_items)

    if cursor is None:
        offset = 0
    else:
        offset = _decode_cursor(cursor)
        if offset > total:
            raise ValidationError("invalid cursor")

    slice_items = sorted_items[offset : offset + limit]
    next_offset = offset + len(slice_items)

    next_cursor: str | None
    if next_offset < total:
        next_cursor = _encode_cursor(next_offset)
    else:
        next_cursor = None

    return Page(items=slice_items, next_cursor=next_cursor)