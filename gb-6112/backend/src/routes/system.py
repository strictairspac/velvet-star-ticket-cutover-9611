from fastapi import APIRouter, Depends, Query
from sqlalchemy import text

from src.config.resources import cache, engine
from src.controllers.access import identity
from src.domain.scenario import CONFIG
from src.services.audit import history

router = APIRouter(tags=["System"])


@router.get("/health")
def health():
    with engine.connect() as db:
        db.execute(text("SELECT 1"))
    cache.ping()
    return {"status": "healthy", "engine": engine.dialect.name}


@router.get("/workbench")
def workbench():
    return {**CONFIG, "engine": "PostgreSQL 16" if engine.dialect.name == "postgresql" else "MySQL 8.0"}


@router.get("/audit", dependencies=[Depends(identity)])
def recent_events(limit: int = Query(default=25, ge=1, le=100)):
    with engine.connect() as db:
        return history(db, limit)
