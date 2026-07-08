import secrets

from motor.motor_asyncio import AsyncIOMotorDatabase
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers.structs import PublicKeyCredentialDescriptor

from core.exceptions import BadRequestException, NotFoundException
from core.redis_client import delete_challenge, get_challenge, set_challenge
from core.security import create_access_token, create_refresh_token, hash_password
from core.settings import settings

RP_ID = settings.RP_ID
RP_NAME = settings.RP_NAME
ORIGIN = settings.ORIGIN


async def start_registration(email: str, db: AsyncIOMotorDatabase) -> dict:
    user = await db.users.find_one({"email": email})
    if not user:
        raise NotFoundException("User")

    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=email.encode("utf-8"),
        user_name=email,
        user_display_name=email,
    )
    set_challenge(email, options.challenge)

    import json

    return json.loads(options_to_json(options))


async def verify_registration(email: str, response: dict, db: AsyncIOMotorDatabase) -> dict:
    expected_challenge = get_challenge(email)
    if not expected_challenge:
        raise BadRequestException("No active challenge")

    try:
        verification = verify_registration_response(
            credential=response,
            expected_challenge=expected_challenge,
            expected_origin=ORIGIN,
            expected_rp_id=RP_ID,
        )
    except Exception as e:
        raise BadRequestException(str(e)) from e

    # Scramble password so only passkey login works
    scrambled = hash_password(secrets.token_hex(64))

    await db.users.update_one(
        {"email": email},
        {
            "$set": {
                "credential_id": verification.credential_id.hex(),
                "public_key": verification.credential_public_key.hex(),
                "password": scrambled,
            }
        },
    )
    delete_challenge(email)

    user = await db.users.find_one({"email": email})
    token_data = {
        "sub": email,
        "role": user.get("role"),
        "hospital_id": user.get("hospital_id"),
    }
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
    }


async def start_login(email: str, db: AsyncIOMotorDatabase) -> dict:
    user = await db.users.find_one({"email": email})
    if not user or not user.get("credential_id"):
        raise BadRequestException("No passkey found")

    options = generate_authentication_options(
        rp_id=RP_ID,
        allow_credentials=[PublicKeyCredentialDescriptor(id=bytes.fromhex(user["credential_id"]))],
    )
    set_challenge(email, options.challenge)

    import json

    return json.loads(options_to_json(options))


async def verify_login(email: str, response: dict, db: AsyncIOMotorDatabase) -> dict:
    user = await db.users.find_one({"email": email})
    if not user or not user.get("credential_id"):
        raise BadRequestException("No passkey found")

    expected_challenge = get_challenge(email)
    if not expected_challenge:
        raise BadRequestException("No active challenge")

    try:
        verify_authentication_response(
            credential=response,
            expected_challenge=expected_challenge,
            expected_rp_id=RP_ID,
            expected_origin=ORIGIN,
            credential_public_key=bytes.fromhex(user["public_key"]),
            credential_current_sign_count=0,
        )
    except Exception as e:
        print(f"WebAuthn verify error: {e}", flush=True)
        raise BadRequestException(str(e)) from e

    delete_challenge(email)

    token_data = {
        "sub": email,
        "role": user.get("role"),
        "hospital_id": user.get("hospital_id"),
    }
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
    }
