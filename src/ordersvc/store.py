"""In-memory KV store — see SPEC.md AC-24..AC-25."""
from __future__ import annotations

from typing import Any, Iterator


class MemoryStore:
    """A simple in-memory key/value store.

    Instances are independent (each has its own dict); no global shared
    state is implied by the class itself. A module-level `default_store`
    instance is provided below for convenience.
    """

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    def put(self, key: str, value: Any) -> None:
        self._data[key] = value

    def get(self, key: str) -> Any:
        try:
            return self._data[key]
        except KeyError:
            raise KeyError(key) from None

    def delete(self, key: str) -> None:
        try:
            del self._data[key]
        except KeyError:
            raise KeyError(key) from None

    def values(self) -> list[Any]:
        """Return a snapshot list of all stored values (for scans)."""
        return list(self._data.values())

    def keys(self) -> list[str]:
        """Return a snapshot list of all stored keys."""
        return list(self._data.keys())

    def items(self) -> list[tuple[str, Any]]:
        """Return a snapshot list of all (key, value) pairs."""
        return list(self._data.items())

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def __iter__(self) -> Iterator[Any]:
        return iter(self.values())

    def __len__(self) -> int:
        return len(self._data)


# Module-level default instance for convenience; not required to be used.
default_store = MemoryStore()
