"""Token auth — see SPEC.md AC-01..AC-04."""
from __future__ import annotations

import secrets
import time
from typing import Dict

from ordersvc.errors import OrdersvcError, TokenExpired, TokenRevoked


class _TokenRecord:
    __slots__ = ("user_id", "expiry", "revoked")

    def __init__(self, user_id: str, expiry: float):
        self.user_id = user_id
        self.expiry = expiry
        self.revoked = False


_REGISTRY: Dict[str, _TokenRecord] = {}


def issue_token(user_id: str, ttl_seconds: int = 3600, *, now: float | None = None) -> str:
    if now is None:
        now = time.time()
    token = secrets.token_urlsafe(32)
    _REGISTRY[token] = _TokenRecord(user_id=user_id, expiry=now + ttl_seconds)
    return token


def verify_token(token: str, *, now: float | None = None) -> str:
    if now is None:
        now = time.time()
    record = _REGISTRY.get(token)
    if record is None:
        raise OrdersvcError("unknown token")
    if record.revoked:
        raise TokenRevoked("token has been revoked")
    if now >= record.expiry:
        raise TokenExpired("token has expired")
    return record.user_id


def revoke_token(token: str) -> None:
    record = _REGISTRY.get(token)
    if record is not None:
        record.revoked = True


def _reset() -> None:
    """Test hook: clear all issued tokens."""
    _REGISTRY.clear()