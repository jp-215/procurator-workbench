"""Domain data structures — Order and Page.

Pure data structures only. No storage, validation, or side effects here.
See SPEC.md AC-05, AC-08, AC-16..AC-19 for behavior that depends on these shapes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Order:
    id: str = ""
    user_id: str = ""
    items: list[dict[str, Any]] = field(default_factory=list)
    status: str = "pending"
    created_at: float = 0.0
    idempotency_key: str | None = None

    @property
    def total(self) -> float:
        return round(sum(item["qty"] * item["unit_price"] for item in self.items), 2)


@dataclass
class Page:
    items: list[Any] = field(default_factory=list)
    next_cursor: str | None = None
