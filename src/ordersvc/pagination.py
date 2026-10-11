"""Cursor pagination — see SPEC.md AC-16..AC-19."""
from __future__ import annotations

import base64
import binascii
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Page:
    items: list[Any] = field(default_factory=list)
    next_cursor: str | None = None


def _field(obj: Any, name: str) -> Any:
    """Read ``name`` from ``obj`` supporting attribute access and mappings."""
    try:
        return getattr(obj, name)
    except AttributeError:
        pass
    try:
        return obj[name]
    except Exception as exc:  # pragma: no cover - defensive
        raise AttributeError(
            f"object {obj!r} has no {name!r} attribute or key"
        ) from exc


def _sort_key(obj: Any) -> tuple:
    created_at = _field(obj, "created_at")
    ident = _field(obj, "id")
    return (_norm(created_at), _norm(ident))


def _norm(value: Any) -> Any:
    """Normalise a key component so cursors round-trip through JSON."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return float(value)
    return str(value)


def _encode_cursor(key: tuple) -> str:
    created_at, ident = key
    payload = json.dumps([created_at, ident], separators=(",", ":"), sort_keys=True)
    raw = base64.urlsafe_b64encode(payload.encode("utf-8"))
    return raw.decode("ascii").rstrip("=")


def _decode_cursor(cursor: str) -> tuple:
    if not isinstance(cursor, str):
        raise ValueError("invalid cursor")
    padding = "=" * (-len(cursor) % 4)
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii") + padding.encode("ascii"))
        data = json.loads(raw.decode("utf-8"))
    except (ValueError, binascii.Error, UnicodeDecodeError) as exc:
        raise ValueError(f"invalid cursor: {cursor!r}") from exc
    if not isinstance(data, list) or len(data) != 2:
        raise ValueError(f"invalid cursor: {cursor!r}")
    return (_norm(data[0]), _norm(data[1]))


def _after(key: tuple, cursor_key: tuple) -> bool:
    """True when ``key`` sorts strictly after ``cursor_key``."""
    for a, b in zip(key, cursor_key):
        if type(a) is not type(b):
            a, b = str(a), str(b)
        if a != b:
            return a > b
    return False


def paginate(items: list[Any], limit: int, cursor: str | None = None) -> Page:
    """Return at most ``limit`` items ordered by (created_at asc, id asc).

    ``cursor`` is an opaque token produced by a previous call; the returned page
    starts strictly after the element it encodes.  ``next_cursor`` is ``None``
    once the collection is exhausted.
    """
    ordered = sorted(items or [], key=_sort_key)

    if cursor is not None:
        cursor_key = _decode_cursor(cursor)
        ordered = [obj for obj in ordered if _after(_sort_key(obj), cursor_key)]

    try:
        limit = int(limit)
    except (TypeError, ValueError):
        raise ValueError("limit must be an integer")

    if limit <= 0:
        return Page(items=[], next_cursor=cursor if ordered else None)

    selected = ordered[:limit]
    exhausted = len(ordered) <= limit

    if not selected or exhausted:
        next_cursor = None
    else:
        next_cursor = _encode_cursor(_sort_key(selected[-1]))

    return Page(items=selected, next_cursor=next_cursor)