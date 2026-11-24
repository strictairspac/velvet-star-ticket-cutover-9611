from time import time

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.domain.collation import isolated_tables
from src.domain.repairs import plan
from src.domain.tickets import ID, merged_tickets, supplement_ticket, ticket_item, unique_tickets
from src.models.cases import cases
from src.models.tickets import case_publications, case_supplements, ticket_issues
from src.services import audit
from src.utils.serial import content_digest

MAX_TICKETS = 250


class BudgetError(ValueError):
    def __init__(self, required, budget):
        super().__init__(f"需要改号 {required} 张，预算 {budget} 张；本次未发布，请调整后重试")
        self.required = required
        self.budget = budget


class NotFound(LookupError):
    pass


class AlreadySwitched(Exception):
    pass


def load_case(db, case_id, lock=False):
    """Return the case row; locking it serializes publication and supplement writes."""
    statement = select(cases).where(cases.c.id == case_id)
    if lock:
        statement = statement.with_for_update()
    return db.execute(statement).mappings().first()


def supplements(db, case_id):
    return [dict(row) for row in db.execute(
        select(case_supplements).where(case_supplements.c.case_id == case_id)
        .order_by(case_supplements.c.serial, case_supplements.c.ticket_id)
    ).mappings()]


def supplement_tickets(rows):
    """Supplement rows in the same shape as volume tickets."""
    return [supplement_ticket(row) for row in rows]


def publication(db, case_id, current=False):
    statement = select(case_publications).where(case_publications.c.case_id == case_id)
    if current:
        statement = statement.with_for_update()
    row = db.execute(statement).mappings().first()
    return dict(row) if row else None


def publications(db):
    """One summary row per switched volume, for the case directory."""
    return [dict(row) for row in db.execute(
        select(case_publications).order_by(case_publications.c.case_id)
    ).mappings()]


def issues(db, case_id):
    """Issued numbers for one volume.

    The join against case_publications means a technician never sees part of a
    volume: either the publication header and every ticket row commit together,
    or nothing is returned. It also hides any row left by an interrupted switch.
    """
    rows = db.execute(
        select(ticket_issues)
        .join(case_publications, case_publications.c.case_id == ticket_issues.c.case_id)
        .where(ticket_issues.c.case_id == case_id)
        .order_by(ticket_issues.c.serial, ticket_issues.c.ticket_id)
    ).mappings()
    return [dict(row) for row in rows]


def ledger(db, ticket_id=None, workshop=None, code=None):
    """The always-available source ledger: old number -> ticket -> volume.

    Volume tickets live in the case payload and supplements in their own table;
    both are folded into one list so the mapping never depends on publication.
    """
    entries = {}
    for row in db.execute(select(cases)).mappings():
        for item in row["payload"].get("tickets", []):
            ticket = supplement_ticket(item)
            if _matches(ticket, ticket_id, workshop, code):
                entries[(row["id"], ticket.id)] = _entry(row["id"], row["code"], row["title"], ticket)
    statement = (
        select(case_supplements, cases.c.code.label("case_code"), cases.c.title.label("case_title"))
        .join(cases, cases.c.id == case_supplements.c.case_id)
        .order_by(case_supplements.c.case_id, case_supplements.c.serial, case_supplements.c.ticket_id)
    )
    for row in db.execute(statement).mappings():
        ticket = supplement_ticket(row)
        if _matches(ticket, ticket_id, workshop, code):
            entries[(row["case_id"], ticket.id)] = _entry(
                row["case_id"], row["case_code"], row["case_title"], ticket)
    for row in db.execute(
        select(ticket_issues)
        .join(case_publications, case_publications.c.case_id == ticket_issues.c.case_id)
        .where(ticket_issues.c.case_id.in_([key[0] for key in entries] or [""]))
    ).mappings():
        entry = entries.get((row["case_id"], row["ticket_id"]))
        if entry is None:
            continue
        entry["new_code"] = row["new_code"]
        entry["action"] = row["action"]
        entry["issued_at"] = row["issued_at"]
        entry["published"] = True
    return sorted(entries.values(), key=lambda item: (item["case_id"], item["serial"], item["ticket_id"]))


def _matches(ticket, ticket_id, workshop, code):
    if ticket_id is not None and ticket.id != ticket_id:
        return False
    if workshop is not None and ticket.workshop != workshop:
        return False
    if code is not None and ticket.code != code:
        return False
    return True


def _entry(case_id, case_code, case_title, ticket):
    return {
        "case_id": case_id, "case_code": case_code, "case_title": case_title,
        "ticket_id": ticket.id, "workshop": ticket.workshop, "old_code": ticket.code,
        "serial": ticket.serial, "new_code": None, "action": None, "issued_at": None,
        "published": False,
    }


def register_supplements(db, case_id, items, actor, now=None):
    """Register supplementary tickets while the volume is still being prepared."""
    now = int(time()) if now is None else now
    case = load_case(db, case_id, lock=True)
    if case is None:
        raise NotFound("资料不存在")
    if publication(db, case_id, current=True) is not None:
        raise AlreadySwitched("该卷已完成切换，不能再登记补票")
    tickets = unique_tickets(ticket_item(item) for item in items)
    known = {ticket.id: ticket for ticket in supplement_tickets(case["payload"].get("tickets", []))}
    known.update({row["ticket_id"]: supplement_ticket(row) for row in supplements(db, case_id)})
    codes = {(ticket.workshop, ticket.code) for ticket in known.values()}
    added = []
    for ticket in tickets:
        current = known.get(ticket.id)
        if current is not None:
            if current == ticket:
                continue
            raise ValueError("补票工票 ID 已登记，不能改换内容")
        if (ticket.workshop, ticket.code) in codes:
            raise ValueError("补票票号与该卷同间已有票号重复")
        known[ticket.id] = ticket
        codes.add((ticket.workshop, ticket.code))
        added.append(ticket)
    if len(known) > MAX_TICKETS:
        raise ValueError(f"每卷工票与补票合计不能超过 {MAX_TICKETS} 张")
    if added:
        try:
            db.execute(case_supplements.insert(), [
                {"case_id": case_id, "ticket_id": ticket.id, "workshop": ticket.workshop,
                 "code": ticket.code, "serial": ticket.serial, "created_at": now}
                for ticket in added
            ])
        except IntegrityError as exc:
            raise ValueError("补票重复登记") from exc
        audit.record(db, "supplement", actor, "case", case_id)
    return supplements(db, case_id)


def publish(db, case_id, parameter, actor, now=None):
    """Switch one whole volume to official numbers in a single transaction.

    The case row lock serializes concurrent publications: the loser re-reads the
    winner's publication and returns it unchanged. Every ticket row and the
    publication header commit together, so an interrupted switch leaves nothing
    behind and a retry plans the same deterministic numbers again.

    Returns (publication, created). ``created`` is False when the volume had
    already been switched; the issued numbers are never regenerated.
    """
    now = int(time()) if now is None else now
    case = load_case(db, case_id, lock=True)
    if case is None:
        raise NotFound("资料不存在")
    current = publication(db, case_id, current=True)
    if current is not None:
        return {**current, "issues": issues(db, case_id)}, False

    tickets = merged_tickets(case["payload"], supplements(db, case_id))
    with isolated_tables(db) as tables:
        tables.source_rows(tickets)
        planned = plan(tables, tickets, parameter)
    if not planned.permitted:
        raise BudgetError(planned.required, parameter)

    rows = [{
        "case_id": case_id, "ticket_id": ticket.id, "workshop": ticket.workshop,
        "old_code": ticket.code, "new_code": proposed, "serial": ticket.serial,
        "action": "改号" if action != "保留" else "保留", "issued_at": now,
    } for ticket, proposed, action in planned.rows]
    # Digest covers only the numbers themselves, so a retry after an interrupted
    # attempt produces the same evidence regardless of timestamps.
    digest = content_digest([{
        "ticket_id": row["ticket_id"], "workshop": row["workshop"],
        "old_code": row["old_code"], "new_code": row["new_code"], "action": row["action"],
    } for row in rows])
    header = {
        "case_id": case_id, "actor": actor, "published_at": now, "parameter": parameter,
        "ticket_count": len(rows), "collision_count": planned.collision_count,
        "changed_count": planned.required, "verified_count": planned.verified_count,
        "digest": digest,
    }
    try:
        # Without a publication header any existing rows were never officially
        # issued (for example a manually inserted leftover); clear them so the
        # retry can write the one authoritative set.
        db.execute(ticket_issues.delete().where(ticket_issues.c.case_id == case_id))
        db.execute(ticket_issues.insert(), rows)
        db.execute(case_publications.insert().values(**header))
        audit.record(db, "publish", actor, "case", case_id)
    except IntegrityError as exc:
        # A publication raced in before the lock was observed. Re-read it in a
        # fresh transaction instead of minting a second set of numbers.
        if not _is_duplicate(exc):
            raise
        raise ConcurrentPublication(case_id) from exc
    return {**header, "issues": issues(db, case_id)}, True


class ConcurrentPublication(Exception):
    def __init__(self, case_id):
        super().__init__("该卷已由另一批次完成切换")
        self.case_id = case_id


def _is_duplicate(exc):
    return bool(exc.orig and exc.orig.args and exc.orig.args[0] == 1062)


def normalise_ticket_id(value):
    return value if ID.fullmatch(value or "") else None
