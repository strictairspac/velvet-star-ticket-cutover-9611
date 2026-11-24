from sqlalchemy import BigInteger, Column, Integer, String, Table
from .base import metadata


audit = Table(
    "audit_events", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("action", String(32), nullable=False),
    Column("actor", String(48), nullable=False),
    Column("entity", String(24), nullable=False),
    Column("entity_id", Integer, nullable=False),
    Column("created_at", BigInteger, nullable=False),
)
