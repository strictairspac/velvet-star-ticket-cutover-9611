import re
from dataclasses import dataclass

ID = re.compile(r"[A-Z0-9]{1,16}")
MAX_TICKETS = 250


@dataclass(frozen=True)
class Ticket:
    id: str
    workshop: str
    code: str
    serial: int


def ticket_item(item):
    """Validate one ticket record and return a Ticket.

    The same shape is used for the original volume and for supplementary
    tickets registered while a case is being prepared.
    """
    if not isinstance(item, dict) or set(item) != {"id", "workshop", "code", "serial"}:
        raise ValueError("工票字段为 id、workshop、code 和 serial")
    ticket = Ticket(**item)
    if not isinstance(ticket.id, str) or not ID.fullmatch(ticket.id):
        raise ValueError("工票 ID 仅接受 1 到 16 位大写字母或数字")
    if not isinstance(ticket.workshop, str) or not 1 <= len(ticket.workshop) <= 32 or not ticket.workshop.strip():
        raise ValueError("工作间应为 1 到 32 字的名称")
    if not isinstance(ticket.code, str) or not 1 <= len(ticket.code) <= 60 or not ticket.code.strip():
        raise ValueError("源票号应有 1 到 60 字并含可见字符")
    if any(ord(char) < 32 or 0xD800 <= ord(char) <= 0xDFFF for char in ticket.workshop + ticket.code):
        raise ValueError("工作间和票号不可包含控制字符或孤立代理字符")
    if type(ticket.serial) is not int or not 1 <= ticket.serial <= 1_000_000:
        raise ValueError("登记顺序须在 1 到 1,000,000 之间")
    return ticket


def unique_tickets(tickets):
    """Reject duplicate ticket IDs or identical same-workshop source codes."""
    seen_ids, seen_codes = set(), set()
    result = []
    for ticket in tickets:
        if ticket.id in seen_ids or (ticket.workshop, ticket.code) in seen_codes:
            raise ValueError("重复工票 ID 或同间完全相同票号")
        seen_ids.add(ticket.id)
        seen_codes.add((ticket.workshop, ticket.code))
        result.append(ticket)
    return result


def check_capacity(tickets):
    if not 1 <= len(tickets) <= MAX_TICKETS:
        raise ValueError(f"每卷须有 1 到 {MAX_TICKETS} 张工票")


def ticket_rows(payload):
    items = payload.get("tickets") if isinstance(payload, dict) else None
    if not isinstance(items, list) or not 1 <= len(items) <= MAX_TICKETS:
        raise ValueError(f"每卷须有 1 到 {MAX_TICKETS} 张工票")
    return unique_tickets(ticket_item(item) for item in items)


def supplement_ticket(row):
    """Normalise a supplement row (ticket_id column) or a ticket mapping."""
    return ticket_item({
        "id": row["ticket_id"] if "ticket_id" in row else row["id"],
        "workshop": row["workshop"],
        "code": row["code"],
        "serial": row["serial"],
    })


def merged_tickets(payload, supplements):
    """The switch-time snapshot: volume tickets plus registered supplements.

    Supplement rows arrive either as mappings from the case_supplements table or
    as already-validated Ticket values.
    """
    extra = [row if isinstance(row, Ticket) else supplement_ticket(row) for row in supplements]
    tickets = unique_tickets(ticket_rows(payload) + extra)
    check_capacity(tickets)
    return tickets
