from contextlib import contextmanager
from dataclasses import asdict
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

TARGET = "utf8mb4_0900_ai_ci"
BINARY = "utf8mb4_0900_bin"


class TicketTables:
    def __init__(self, db):
        self.db = db
        suffix = uuid4().hex[:12]
        self.source = f"setting_src_{suffix}"
        self.target = f"setting_dst_{suffix}"

    def create(self):
        for table, collation in ((self.source, BINARY), (self.target, TARGET)):
            self.db.execute(text(f"""
                CREATE TEMPORARY TABLE {table} (
                    id VARCHAR(16) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
                    workshop VARCHAR(32) COLLATE {BINARY} NOT NULL,
                    code VARCHAR(60) COLLATE {collation} NOT NULL,
                    serial INT NOT NULL,
                    UNIQUE KEY (workshop, code)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """))

    def source_rows(self, tickets):
        self.db.execute(text(f"""
            INSERT INTO {self.source} (id, workshop, code, serial)
            VALUES (:id, :workshop, :code, :serial)
        """), [asdict(ticket) for ticket in tickets])

    def groups(self):
        rows = self.db.execute(text(f"""
            SELECT id, DENSE_RANK() OVER (
                PARTITION BY workshop ORDER BY code COLLATE {TARGET}
            ) AS group_number
            FROM {self.source}
        """))
        return {row.id: row.group_number for row in rows}

    def try_target(self, ticket, proposed):
        fields = {**asdict(ticket), "code": proposed}
        try:
            with self.db.begin_nested():
                self.db.execute(text(f"""
                    INSERT INTO {self.target} (id, workshop, code, serial)
                    VALUES (:id, :workshop, :code, :serial)
                """), fields)
        except IntegrityError as exc:
            if not exc.orig.args or exc.orig.args[0] != 1062:
                raise
            return False
        return True

    def count(self):
        return self.db.execute(text(f"SELECT COUNT(*) FROM {self.target}")).scalar_one()


@contextmanager
def isolated_tables(db):
    tables = TicketTables(db)
    try:
        tables.create()
        yield tables
    finally:
        for table in (tables.target, tables.source):
            db.execute(text(f"DROP TEMPORARY TABLE IF EXISTS {table}"))
