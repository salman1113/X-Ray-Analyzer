import contextlib
import time
from datetime import UTC, datetime

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from core.database import master_db
from core.security import verify_token


class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    Logs every authenticated API request to the master audit_logs collection.
    Captures: user, tenant, method, path, status, latency.
    """

    SKIP_PATHS = {"/docs", "/redoc", "/openapi.json", "/health"}

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        latency_ms = round((time.perf_counter() - start) * 1000, 2)

        # Extract user info from token (best-effort, no error if missing)
        user_email = None
        tenant_id = None
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            payload = verify_token(auth.split(" ", 1)[1])
            if payload:
                user_email = payload.get("sub")
                tenant_id = payload.get("hospital_id")

        log_entry = {
            "timestamp": datetime.now(UTC),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "latency_ms": latency_ms,
            "user_email": user_email,
            "tenant_id": tenant_id,
            "client_ip": request.client.host if request.client else None,
        }

        # Fire-and-forget insert — never block the response
        with contextlib.suppress(Exception):
            await master_db.audit_logs.insert_one(log_entry)

        return response
