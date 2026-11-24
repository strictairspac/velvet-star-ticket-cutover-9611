from collections import defaultdict


def reserve_codes(tables, tickets):
    groups = tables.groups()
    by_scope = defaultdict(list)
    for ticket in sorted(tickets, key=lambda item: (item.serial, item.id)):
        by_scope[(ticket.workshop, groups[ticket.id])].append(ticket)
    for members in by_scope.values():
        winner = members[0]
        if not tables.try_target(winner, winner.code):
            raise ValueError("分组结果与目标库唯一约束不一致")
    return by_scope


def choose_alias(tables, ticket, population):
    stem = f"R-{ticket.id}"
    for attempt in range(population + 1):
        proposed = f"{stem}-{attempt + 1}" if attempt else stem
        if tables.try_target(ticket, proposed):
            return proposed
    raise ValueError(f"工票 {ticket.id} 未分配到可用别名")


def plan(tables, tickets, budget):
    by_scope = reserve_codes(tables, tickets)
    collision_count = sum(len(group) > 1 for group in by_scope.values())
    required = len(tickets) - len(by_scope)
    permitted = required <= budget
    rows = []
    for group in by_scope.values():
        winner, *displaced = group
        rows.append((winner, winner.code, "保留"))
        for ticket in displaced:
            if tables.try_target(ticket, ticket.code):
                raise ValueError("目标唯一约束未拒绝预期冲突")
            suggestion = choose_alias(tables, ticket, len(tickets)) if permitted else None
            rows.append((ticket, suggestion, "别名已验" if permitted else "待改号预算"))
    count = tables.count()
    if count != (len(tickets) if permitted else len(by_scope)):
        raise ValueError("目标库试写行数和改号计划不一致")
    rows.sort(key=lambda entry: (entry[0].serial, entry[0].id))
    return rows, collision_count, required, count
