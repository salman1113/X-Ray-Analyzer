"""
Application lifecycle events (startup / shutdown).
"""

import contextlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.database import check_connection, client, master_db
from core.redis_client import redis_client

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs on app startup and shutdown."""

    # ── Startup ──
    if not await check_connection():
        raise RuntimeError("MongoDB connection failed — refusing to start")
    logger.info("MongoDB connected")

    # Verify Redis
    try:
        redis_client.ping()
        logger.info("Redis connected")
    except Exception as e:
        raise RuntimeError(f"Redis connection failed: {e}") from e

    # Create indexes (idempotent, wrapped in error handling)
    try:
        await master_db.users.create_index("email", unique=True)
        await master_db.hospitals.create_index("hospital_id", unique=True)
        await master_db.hospitals.create_index("invite_code")
        await master_db.hospitals.create_index("subdomain", unique=True, sparse=True)
        logger.info("Database indexes ensured")
    except Exception as e:
        logger.error("Index creation failed: %s", e)
        raise RuntimeError(f"Failed to create database indexes: {e}") from e

    yield

    # ── Shutdown ──
    logger.info("Shutting down...")
    client.close()
    with contextlib.suppress(Exception):
        redis_client.close()
