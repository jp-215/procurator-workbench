"""Retry with exponential backoff — see SPEC.md AC-20..AC-23."""
from __future__ import annotations

import time
from typing import Any, Callable

from ordersvc.errors import TransientError


def retry_with_backoff(
    fn: Callable[[], Any],
    max_attempts: int = 3,
    base_delay: float = 0.1,
    sleep: Callable[[float], None] = time.sleep,
) -> Any:
    last_error: TransientError | None = None
    for attempt in range(max_attempts):
        try:
            return fn()
        except TransientError as exc:
            last_error = exc
            if attempt < max_attempts - 1:
                sleep(base_delay * 2 ** attempt)
    assert last_error is not None
    raise last_error