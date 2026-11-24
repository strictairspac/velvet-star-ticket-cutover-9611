from sqlalchemy import Column, String, Table
from .base import metadata


users = Table(
    "users", metadata,
    Column("username", String(48), primary_key=True),
    Column("role", String(16), nullable=False),
    Column("password_hash", String(180), nullable=False),
)
