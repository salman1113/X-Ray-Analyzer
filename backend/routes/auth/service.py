"""
Authentication business logic — register, login, OTP, refresh.
"""

import logging
import secrets
import uuid

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from core.database import setup_tenant_database
from core.exceptions import (
    BadRequestException,
    ConflictException,
    NotAuthenticatedException,
)
from core.redis_client import check_rate_limit, delete_otp, get_otp, set_otp
from core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)
from core.tenancy import build_tenant_url, is_reserved, slugify

logger = logging.getLogger(__name__)

_FALLBACK_SLUG = "hospital"
_MAX_SUFFIX_TRIES = 50
_OTP_MAX_ATTEMPTS = 5
_OTP_ATTEMPT_WINDOW = 600  # 10 minutes


def _generate_otp() -> str:
    """Generate a cryptographically secure 6-digit OTP."""
    return str(secrets.randbelow(900000) + 100000)


async def _generate_unique_subdomain(hospital_name: str, db: AsyncIOMotorDatabase) -> str:
    """
    Derive a DNS-safe slug from hospital_name, ensure uniqueness.
    Uses the unique index on hospitals.subdomain as the final guard.
    """
    base = slugify(hospital_name) or _FALLBACK_SLUG
    if is_reserved(base):
        base = f"{_FALLBACK_SLUG}-{secrets.token_hex(3)}"

    candidate = base
    for n in range(2, _MAX_SUFFIX_TRIES + 2):
        existing = await db.hospitals.find_one({"subdomain": candidate})
        if not existing and not is_reserved(candidate):
            return candidate
        candidate = f"{base}-{n}"

    return f"{base}-{secrets.token_hex(3)}"


async def register_user(
    email: str,
    password: str,
    role: str,
    hospital_name: str | None,
    invite_code: str | None,
    db: AsyncIOMotorDatabase,
) -> dict:
    """Register a new user. Returns dict with otp_code + tenant info."""
    existing = await db.users.find_one({"email": email})
    if existing and existing.get("is_verified"):
        raise ConflictException("User already exists. Please login.")

    hashed = hash_password(password)
    hospital_id: str | None = None
    subdomain: str | None = None
    tenant_url: str | None = None
    effective_role = role

    if role == "hospital":
        if not hospital_name:
            raise BadRequestException("Hospital name is required.")

        hospital_id = str(uuid.uuid4())
        invite = str(uuid.uuid4())[:8].upper()
        subdomain = await _generate_unique_subdomain(hospital_name, db)
        tenant_url = build_tenant_url(subdomain)

        await setup_tenant_database(hospital_id)

        await db.hospitals.insert_one(
            {
                "hospital_id": hospital_id,
                "name": hospital_name.strip(),
                "subdomain": subdomain,
                "invite_code": invite,
                "plan": "free",
                "max_users": 5,
                "max_scans_per_month": 100,
                "is_active": True,
            }
        )
        effective_role = "admin"

    elif role == "doctor":
        if not invite_code:
            raise BadRequestException("Invite code is required.")
        hospital = await db.hospitals.find_one({"invite_code": invite_code.strip()})
        if not hospital:
            raise BadRequestException("Invalid invite code.")
        hospital_id = hospital["hospital_id"]
        subdomain = hospital.get("subdomain")
        if subdomain:
            tenant_url = build_tenant_url(subdomain)
        effective_role = "doctor"

    # Upsert user (handles race condition on concurrent registration)
    user_doc = {
        "email": email,
        "password": hashed,
        "is_verified": False,
        "credential_id": None,
        "public_key": None,
        "role": effective_role,
        "hospital_id": hospital_id,
    }
    if not existing:
        await db.users.insert_one(user_doc)
    else:
        await db.users.update_one(
            {"email": email},
            {
                "$set": {
                    "password": hashed,
                    "role": effective_role,
                    "hospital_id": hospital_id,
                }
            },
        )

    otp_code = _generate_otp()
    set_otp(email, otp_code)

    return {
        "otp_code": otp_code,
        "subdomain": subdomain,
        "tenant_url": tenant_url,
        "hospital_id": hospital_id,
    }


async def verify_otp_and_activate(email: str, otp: str, db: AsyncIOMotorDatabase) -> dict:
    """Verify OTP, activate user, return tokens."""
    # Rate-limit OTP attempts to prevent brute force
    rate_key = f"otp_attempt:{email}"
    if not check_rate_limit(rate_key, _OTP_MAX_ATTEMPTS, _OTP_ATTEMPT_WINDOW):
        raise BadRequestException("Too many attempts. Please request a new OTP.")

    stored = get_otp(email)
    if not stored:
        raise BadRequestException("OTP expired or invalid")
    if not secrets.compare_digest(stored, otp):
        raise BadRequestException("Incorrect OTP")

    # Atomic update + fetch
    user = await db.users.find_one_and_update(
        {"email": email},
        {"$set": {"is_verified": True}},
        return_document=ReturnDocument.AFTER,
    )
    if not user:
        raise BadRequestException("User not found")

    delete_otp(email)

    subdomain = None
    tenant_url = None
    hospital_id = user.get("hospital_id")
    if hospital_id:
        hospital = await db.hospitals.find_one({"hospital_id": hospital_id})
        if hospital:
            subdomain = hospital.get("subdomain")
            if subdomain:
                tenant_url = build_tenant_url(subdomain)

    token_data = {
        "sub": email,
        "role": user.get("role"),
        "hospital_id": hospital_id,
    }
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "has_passkey": bool(user.get("credential_id")),
        "subdomain": subdomain,
        "tenant_url": tenant_url,
    }


async def login_user(email: str, password: str, db: AsyncIOMotorDatabase) -> dict:
    """Password-based login."""
    # Rate-limit login attempts per email
    rate_key = f"login_attempt:{email}"
    if not check_rate_limit(rate_key, 10, 300):
        raise NotAuthenticatedException("Too many login attempts. Try again later.")

    user = await db.users.find_one({"email": email})

    # Uniform error message to prevent user enumeration
    if not user or not verify_password(password, user["password"]):
        raise NotAuthenticatedException("Invalid email or password")

    if not user.get("is_verified"):
        raise BadRequestException("Account not verified. Register again to get OTP.")

    subdomain = None
    tenant_url = None
    hospital_id = user.get("hospital_id")
    if hospital_id:
        hospital = await db.hospitals.find_one({"hospital_id": hospital_id})
        if hospital:
            subdomain = hospital.get("subdomain")
            if subdomain:
                tenant_url = build_tenant_url(subdomain)

    token_data = {
        "sub": email,
        "role": user.get("role"),
        "hospital_id": hospital_id,
    }
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "has_passkey": bool(user.get("credential_id")),
        "subdomain": subdomain,
        "tenant_url": tenant_url,
    }


async def refresh_access_token(refresh_token: str, db: AsyncIOMotorDatabase) -> dict:
    """Issue new tokens from a valid refresh token."""
    payload = verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise NotAuthenticatedException("Invalid refresh token")

    email = payload.get("sub")
    user = await db.users.find_one({"email": email})
    if not user:
        raise NotAuthenticatedException("User not found")

    token_data = {
        "sub": email,
        "role": user.get("role"),
        "hospital_id": user.get("hospital_id"),
    }
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
    }


async def get_user_profile(user: dict, db: AsyncIOMotorDatabase) -> dict:
    """Get current user's profile with hospital info."""
    response = {
        "email": user["email"],
        "role": user["role"],
        "hospital_id": user.get("tenant_id"),
    }

    if user.get("tenant_id"):
        hospital = await db.hospitals.find_one({"hospital_id": user["tenant_id"]})
        if hospital:
            response["hospital_name"] = hospital.get("name")
            response["subdomain"] = hospital.get("subdomain")
            if hospital.get("subdomain"):
                response["tenant_url"] = build_tenant_url(hospital["subdomain"])
            if user["role"] in ("admin", "superadmin"):
                response["invite_code"] = hospital.get("invite_code")

    return response
