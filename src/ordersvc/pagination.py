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
    """Fetch a field from either a dict-like item or an object with attributes."""
    if isinstance(item, dict):
        if name not in item:
            raise ValidationError(f"item missing field {name!r}")
        return item[name]
    if hasattr(item, name):
        return getattr(item, name)
    raise ValidationError(f"item missing field {name!r}")


def _sort_key(item: Any) -> tuple[Any, Any]:
    return (_get_field(item, "created_at"), _get_field(item, "id"))


def _encode_cursor(created_at: Any, id_: Any) -> str:
    payload = json.dumps({"created_at": created_at, "id": id_}, separators=(",", ":"))
    raw = payload.encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def _decode_cursor(cursor: str) -> tuple[Any, Any]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii"))
        payload = json.loads(raw.decode("utf-8"))
        created_at = payload["created_at"]
        id_ = payload["id"]
    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError("malformed cursor") from exc
    return created_at, id_


def paginate(items: list[Any], limit: int, cursor: str | None = None) -> Page:
    if limit <= 0:
        raise ValidationError("limit must be > 0")

    sorted_items = sorted(items, key=_sort_key)

    start_idx = 0
    if cursor is not None:
        boundary = _decode_cursor(cursor)
        start_idx = len(sorted_items)
        for i, item in enumerate(sorted_items):
            if _sort_key(item) > boundary:
                start_idx = i
                break

    slice_items = sorted_items[start_idx:start_idx + limit]
    next_idx = start_idx + len(slice_items)

    next_cursor: str | None = None
    if next_idx < len(sorted_items) and slice_items:
        last = slice_items[-1]
        next_cursor = _encode_cursor(
            _get_field(last, "created_at"), _get_field(last, "id")
        )

    return Page(items=slice_items, next_cursor=next_cursor)