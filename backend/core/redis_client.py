import redis

from core.settings import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


# ── OTP ──────────────────────────────────────────────────────────────────────


def set_otp(email: str, code: str, ttl: int = 600):
    """Store OTP in Redis with a TTL (default 10 mins)."""
    redis_client.setex(f"otp:{email}", ttl, code)


def get_otp(email: str) -> str | None:
    """Retrieve OTP from Redis."""
    return redis_client.get(f"otp:{email}")


def delete_otp(email: str):
    """Delete OTP from Redis after verification."""
    redis_client.delete(f"otp:{email}")


# ── WebAuthn Challenges ─────────────────────────────────────────────────────


def set_challenge(email: str, challenge: bytes, ttl: int = 300):
    """Store WebAuthn challenge in Redis (5 mins TTL)."""
    redis_client.setex(f"challenge:{email}", ttl, challenge.hex())


def get_challenge(email: str) -> bytes | None:
    """Retrieve WebAuthn challenge from Redis."""
    val = redis_client.get(f"challenge:{email}")
    return bytes.fromhex(val) if val else None


def delete_challenge(email: str):
    """Delete challenge from Redis."""
    redis_client.delete(f"challenge:{email}")


# ── Token Blacklist ──────────────────────────────────────────────────────────


def blacklist_token(jti: str, ttl: int = 86400):
    """Add a token ID to the blacklist (default 24h TTL)."""
    redis_client.setex(f"blacklist:{jti}", ttl, "1")


def is_token_blacklisted(jti: str) -> bool:
    """Check if a token has been revoked."""
    return redis_client.exists(f"blacklist:{jti}") > 0


# ── Rate Limiting ────────────────────────────────────────────────────────────


def check_rate_limit(key: str, max_requests: int, window_seconds: int) -> bool:
    """
    Returns True if within limit, False if exceeded.
    Uses a simple sliding-window counter.
    """
    current = redis_client.get(f"rate:{key}")
    if current and int(current) >= max_requests:
        return False
    pipe = redis_client.pipeline()
    pipe.incr(f"rate:{key}")
    pipe.expire(f"rate:{key}", window_seconds)
    pipe.execute()
    return True
