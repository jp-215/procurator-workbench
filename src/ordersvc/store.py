"""In-memory KV store — see SPEC.md AC-24..AC-25."""
from __future__ import annotations

from typing import Any, ItemsView, Iterator, ValuesView


class MemoryStore:
    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    def put(self, key: str, value: Any) -> None:
        self._data[key] = value

    def get(self, key: str) -> Any:
        return self._data[key]

    def delete(self, key: str) -> None:
        del self._data[key]

    def values(self) -> ValuesView[Any]:
        return self._data.values()

    def items(self) -> ItemsView[str, Any]:
        return self._data.items()

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def clear(self) -> None:
        self._data.clear()


default_store = MemoryStore()
