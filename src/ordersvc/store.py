"""In-memory KV store — see SPEC.md AC-24..AC-25."""
from __future__ import annotations

from typing import Any, Dict


class MemoryStore:
    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}

    def put(self, key: str, value: Any) -> None:
        self._data[key] = value

    def get(self, key: str) -> Any:
        return self._data[key]

    def delete(self, key: str) -> None:
        del self._data[key]


# Shared default instance for other modules to use.
default_store = MemoryStore()