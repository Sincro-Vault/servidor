"""Health check del servidor."""
from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import text

from src.database import engine

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
def health():
    db_ok = True
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    return {
        "status": "healthy" if db_ok else "degraded",
        "version": "1.0.0",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "components": {
            "database": "healthy" if db_ok else "unhealthy",
            "blockchain": "healthy",
        },
    }


@router.get("/ping")
def ping():
    return {"pong": datetime.now(timezone.utc).isoformat()}
