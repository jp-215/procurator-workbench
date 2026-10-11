"""In-memory KV store — see SPEC.md AC-24..AC-25."""
from __future__ import annotations

from typing import Any, Iterator


class MemoryStore:
    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    def put(self, key: str, value: Any) -> None:
        self._data[key] = value

    def get(self, key: str) -> Any:
        return self._data[key]

    def delete(self, key: str) -> None:
        del self._data[key]

    def values(self) -> Iterator[Any]:
        return iter(self._data.values())

    def items(self) -> Iterator[tuple[str, Any]]:
        return iter(self._data.items())

    def keys(self) -> Iterator[str]:
        return iter(self._data.keys())

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def __len__(self) -> int:
        return len(self._data)