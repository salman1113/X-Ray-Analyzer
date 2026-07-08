"""
FastAPI dependencies — authentication and tenant resolution.

These are injected into route handlers via Depends().
"""

from fastapi import Depends, Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from core.database import get_master_db, get_tenant_database
from core.exceptions import (
    ForbiddenException,
    InvalidTokenException,
    NotAuthenticatedException,
    TenantNotFoundException,
)
from core.security import verify_token


def _extract_token(request: Request) -> str:
    """Pull the Bearer token from the Authorization header."""
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise NotAuthenticatedException()
    return auth.split(" ", 1)[1]


async def get_current_user(
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_master_db),
) -> dict:
    """
    Authenticate the request and return the user's context.
    Used by all protected routes.
    """
    token = _extract_token(request)
    payload = verify_token(token)
    if not payload:
        raise InvalidTokenException()

    email = payload.get("sub")
    if not email:
        raise InvalidTokenException("Token missing subject")

    user = await db.users.find_one({"email": email})
    if not user:
        raise InvalidTokenException("User no longer exists")

    return {
        "user_id": str(user["_id"]),
        "email": user["email"],
        "role": user.get("role", "doctor"),
        "tenant_id": user.get("hospital_id"),
        "is_verified": user.get("is_verified", False),
        "has_passkey": bool(user.get("credential_id")),
    }


async def get_tenant_db(
    user: dict = Depends(get_current_user),
) -> AsyncIOMotorDatabase:
    """
    Returns the tenant's own database.

    Flow: JWT → user → hospital_id → client["tenant_<hospital_id>"]

    All patient/scan routes use this.
    """
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise TenantNotFoundException()
    return get_tenant_database(tenant_id)


# ── Role guards ──────────────────────────────────────────────────────────────


def require_role(*allowed_roles: str):
    """Dependency that checks the user has one of the allowed roles."""

    async def _check(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in allowed_roles:
            raise ForbiddenException(
                f"Role '{user['role']}' not allowed. Need: {', '.join(allowed_roles)}"
            )
        return user

    return _check


require_superadmin = require_role("superadmin")
require_admin = require_role("admin", "superadmin")
require_doctor = require_role("doctor", "admin", "superadmin")
require_any_authenticated = require_role("doctor", "admin", "superadmin", "radiologist")
