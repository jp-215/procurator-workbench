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
    attempt = 0
    while True:
        try:
            return fn()
        except TransientError:
            attempt += 1
            if attempt >= max_attempts:
                raise
            sleep(base_delay * 2 ** (attempt - 1))