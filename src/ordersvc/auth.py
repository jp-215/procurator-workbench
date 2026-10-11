"""Token auth — see SPEC.md AC-01..AC-04."""
from __future__ import annotations

import time
import uuid

from ordersvc.errors import InvalidToken, TokenExpired, TokenRevoked

# Module-level registry: token -> metadata dict
_REGISTRY: dict[str, dict] = {}


def issue_token(user_id: str, ttl_seconds: int = 3600, *, now: float | None = None) -> str:
    if now is None:
        now = time.time()
    token = uuid.uuid4().hex
    _REGISTRY[token] = {
        "user_id": user_id,
        "expiry": now + ttl_seconds,
        "revoked": False,
    }
    return token


def verify_token(token: str, *, now: float | None = None) -> str:
    if now is None:
        now = time.time()
    meta = _REGISTRY.get(token)
    if meta is None:
        raise InvalidToken(f"unknown token: {token!r}")
    if meta["revoked"]:
        raise TokenRevoked(f"token revoked: {token!r}")
    if now >= meta["expiry"]:
        raise TokenExpired(f"token expired: {token!r}")
    return meta["user_id"]


def revoke_token(token: str) -> None:
    meta = _REGISTRY.get(token)
    if meta is None:
        return
    meta["revoked"] = True