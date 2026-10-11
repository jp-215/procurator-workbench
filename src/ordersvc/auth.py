"""Token auth — see SPEC.md AC-01..AC-04."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

from ordersvc.errors import OrderSvcError, TokenExpired, TokenRevoked


@dataclass
class _TokenRecord:
    user_id: str
    expiry: float
    revoked: bool = False


# Module-level registry of issued tokens.
_TOKENS: dict[str, _TokenRecord] = {}


def issue_token(user_id: str, ttl_seconds: int = 3600, *, now: float | None = None) -> str:
    if now is None:
        now = time.time()
    token = uuid.uuid4().hex
    expiry = now + ttl_seconds
    _TOKENS[token] = _TokenRecord(user_id=user_id, expiry=expiry, revoked=False)
    return token


def verify_token(token: str, *, now: float | None = None) -> str:
    if now is None:
        now = time.time()
    record = _TOKENS.get(token)
    if record is None:
        raise OrderSvcError(f"unknown token: {token!r}")
    if record.revoked:
        raise TokenRevoked(f"token revoked: {token!r}")
    if now >= record.expiry:
        raise TokenExpired(f"token expired: {token!r}")
    return record.user_id


def revoke_token(token: str) -> None:
    record = _TOKENS.get(token)
    if record is None:
        raise OrderSvcError(f"unknown token: {token!r}")
    record.revoked = True


def _reset() -> None:
    """Test hook: clear all issued tokens."""
    _TOKENS.clear()