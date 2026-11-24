from time import time
from sqlalchemy import insert, select
from src.models.audit import audit


def record(db, action, actor, entity, entity_id):
    db.execute(insert(audit).values(
        action=action, actor=actor, entity=entity, entity_id=entity_id, created_at=int(time())
    ))


def history(db, limit):
    query = select(audit).order_by(audit.c.id.desc()).limit(limit)
    return [dict(row) for row in db.execute(query).mappings()]
