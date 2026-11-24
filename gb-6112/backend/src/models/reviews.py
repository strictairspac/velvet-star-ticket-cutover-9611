from sqlalchemy import BigInteger, Column, ForeignKey, String, Table
from .base import metadata


reviews = Table(
    "reviews", metadata,
    Column("run_id", ForeignKey("runs.id"), primary_key=True),
    Column("actor", String(48), nullable=False),
    Column("note", String(500), nullable=False),
    Column("created_at", BigInteger, nullable=False),
)
