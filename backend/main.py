import logging
import re

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.events import lifespan
from core.middleware.audit_log import AuditLogMiddleware
from core.middleware.rate_limit import RateLimitMiddleware
from core.middleware.tenant_resolver import TenantResolverMiddleware
from core.settings import settings
from routes.admin.router import router as admin_router
from routes.ai.router import router as ai_router

# Domain routers
from routes.auth.router import router as auth_router
from routes.billing.router import router as billing_router
from routes.passkey.router import router as passkey_router
from routes.patient.router import router as patient_router
from routes.scan.router import router as scan_router
from routes.tenants.router import router as tenant_router
from routes.user.router import router as user_router

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.API_VERSION,
        lifespan=lifespan,
    )

    # ── Middleware (order matters: last added = first executed) ───────────
    # CORS — allow configured origin + any tenant subdomain of BASE_DOMAIN
    escaped_base = re.escape(settings.BASE_DOMAIN)
    tenant_origin_regex = (
        rf"^https?://([a-z0-9]([a-z0-9-]{{0,61}}[a-z0-9])?\.)?{escaped_base}(:\d{{1,5}})?$"
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.ORIGIN],
        allow_origin_regex=tenant_origin_regex,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Tenant-Subdomain",
            "X-Requested-With",
            "Accept",
        ],
    )
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(AuditLogMiddleware)
    app.add_middleware(TenantResolverMiddleware)

    # ── Global exception handler ────────────────────────────────────────
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger = logging.getLogger("uvicorn.error")
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    # ── API v1 Routers ──────────────────────────────────────────────────
    api_prefix = f"/api/{settings.API_VERSION}"

    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(passkey_router, prefix=api_prefix)
    app.include_router(tenant_router, prefix=api_prefix)
    app.include_router(user_router, prefix=api_prefix)
    app.include_router(patient_router, prefix=api_prefix)
    app.include_router(scan_router, prefix=api_prefix)
    app.include_router(ai_router, prefix=api_prefix)
    app.include_router(billing_router, prefix=api_prefix)
    app.include_router(admin_router, prefix=api_prefix)

    # ── Health Check ────────────────────────────────────────────────────
    @app.get("/health")
    async def health():
        return {"status": "ok", "version": settings.API_VERSION}

    return app


app = create_app()
