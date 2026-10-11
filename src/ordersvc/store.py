"""In-memory KV store — see SPEC.md AC-24..AC-25."""
from __future__ import annotations

from typing import Any, Iterator


class MemoryStore:
    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    def put(self, key: str, value: Any) -> None:
        self._data[key] = value

    def get(self, key: str) -> Any:
        if key not in self._data:
            raise KeyError(key)
        return self._data[key]

    def delete(self, key: str) -> None:
        if key not in self._data:
            raise KeyError(key)
        del self._data[key]

    def values(self) -> Iterator[Any]:
        return iter(self._data.values())

    def keys(self) -> Iterator[str]:
        return iter(self._data.keys())

    def items(self) -> Iterator[tuple[str, Any]]:
        return iter(self._data.items())

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def __len__(self) -> int:
        return len(self._data)