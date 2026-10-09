"""Health endpoints used by Cloud Run probes and the uptime check (gcp repo)."""

from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DbSession

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness probe and uptime check: the process is up."""
    return {"status": "ok"}


@router.get("/readyz")
def readyz(db: DbSession) -> dict[str, str]:
    """Startup probe: the database is reachable."""
    db.execute(text("SELECT 1"))
    return {"status": "ready"}
