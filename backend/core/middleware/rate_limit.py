from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from core.redis_client import check_rate_limit
from core.security import verify_token


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Per-IP and per-tenant rate limiting.
    - Anonymous requests: 60 req/min per IP
    - Authenticated requests: 200 req/min per tenant
    """

    ANON_LIMIT = 60
    TENANT_LIMIT = 200
    WINDOW = 60  # seconds

    SKIP_PATHS = {"/docs", "/redoc", "/openapi.json", "/health"}

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        # Determine rate-limit key
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            payload = verify_token(auth.split(" ", 1)[1])
            if payload and payload.get("hospital_id"):
                key = f"tenant:{payload['hospital_id']}"
                limit = self.TENANT_LIMIT
            else:
                key = f"ip:{request.client.host}" if request.client else "ip:unknown"
                limit = self.ANON_LIMIT
        else:
            key = f"ip:{request.client.host}" if request.client else "ip:unknown"
            limit = self.ANON_LIMIT

        if not check_rate_limit(key, limit, self.WINDOW):
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later."},
            )

        return await call_next(request)
