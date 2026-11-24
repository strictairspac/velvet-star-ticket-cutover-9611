import re
from dataclasses import dataclass

ID = re.compile(r"[A-Z0-9]{1,16}")


@dataclass(frozen=True)
class Ticket:
    id: str
    workshop: str
    code: str
    serial: int


def ticket_rows(payload):
    items = payload.get("tickets") if isinstance(payload, dict) else None
    if not isinstance(items, list) or not 1 <= len(items) <= 250:
        raise ValueError("每卷须有 1 到 250 张工票")
    tickets = []
    seen_ids, seen_codes = set(), set()
    for item in items:
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
        if ticket.id in seen_ids or (ticket.workshop, ticket.code) in seen_codes:
            raise ValueError("重复工票 ID 或同间完全相同票号")
        seen_ids.add(ticket.id)
        seen_codes.add((ticket.workshop, ticket.code))
        tickets.append(ticket)
    return tickets
