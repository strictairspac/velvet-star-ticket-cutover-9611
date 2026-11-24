from sqlalchemy import BigInteger, Column, ForeignKey, Index, Integer, String, Table, UniqueConstraint
from .base import metadata

# Source numbers keep the binary collation of the old index; issued numbers use the
# migrated collation. Declaring both on the column means MySQL enforces exactly the
# uniqueness rules the real switch relies on.
BINARY = "utf8mb4_0900_bin"
TARGET = "utf8mb4_0900_ai_ci"


case_supplements = Table(
    "case_supplements", metadata,
    Column("case_id", ForeignKey("cases.id"), primary_key=True),
    Column("ticket_id", String(16, collation=BINARY), primary_key=True),
    Column("workshop", String(32, collation=BINARY), nullable=False),
    Column("code", String(60, collation=BINARY), nullable=False),
    Column("serial", Integer, nullable=False),
    Column("created_at", BigInteger, nullable=False),
    UniqueConstraint("case_id", "workshop", "code", name="uq_case_supplement_code"),
)


case_publications = Table(
    "case_publications", metadata,
    Column("case_id", ForeignKey("cases.id"), primary_key=True),
    Column("actor", String(48), nullable=False),
    Column("published_at", BigInteger, nullable=False),
    Column("parameter", Integer, nullable=False),
    Column("ticket_count", Integer, nullable=False),
    Column("collision_count", Integer, nullable=False),
    Column("changed_count", Integer, nullable=False),
    Column("verified_count", Integer, nullable=False),
    Column("digest", String(64), nullable=False),
)


# One official row per ticket per volume. The (case_id, workshop, new_code)
# unique key is what makes the whole-volume switch atomic and collision-free.
ticket_issues = Table(
    "ticket_issues", metadata,
    Column("case_id", ForeignKey("cases.id"), primary_key=True),
    Column("ticket_id", String(16, collation=BINARY), primary_key=True),
    Column("workshop", String(32, collation=BINARY), nullable=False),
    Column("old_code", String(60, collation=BINARY), nullable=False),
    Column("new_code", String(60, collation=TARGET), nullable=False),
    Column("serial", Integer, nullable=False),
    Column("action", String(16), nullable=False),
    Column("issued_at", BigInteger, nullable=False),
    UniqueConstraint("case_id", "workshop", "new_code", name="uq_ticket_issue_target"),
    Index("ix_ticket_issues_ticket", "ticket_id"),
    Index("ix_ticket_issues_old_code", "old_code"),
)
