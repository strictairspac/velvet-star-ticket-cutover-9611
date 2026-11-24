from .collation import isolated_tables
from .fixtures import FIXTURES
from .repairs import plan
from .tickets import ticket_rows


CONFIG = {
    "title": "绒星镶坊·珠宝镶嵌工票转版",
    "team": "绒星镶坊 14 人制签与镶嵌组",
    "description": "预检票号对照规则变化，定位同间重名并核验旧票保留和别名换发方案。",
    "direction": "排序规则迁移与唯一性",
    "mechanism": "MySQL 真实排序规则分组、目标唯一键试写和别名碰撞重试。",
    "modules": ["转版审阅", "旧票卷宗", "目标试写", "改号交接"],
    "unit": "工票卷",
    "max_parameter": 250,
    "default_parameter": 6,
    "parameter_label": "本次允许改号张数",
    "facts": ["同间唯一", "真实试写", "旧票索引"],
    "palette": 12,
    "fixture": "setting-tickets-north-1124.json",
}


def validate(payload):
    ticket_rows(payload)


def run(payload, parameter, db):
    tickets = ticket_rows(payload)
    with isolated_tables(db) as tables:
        tables.source_rows(tickets)
        planned, collision_count, repair_count, verified_count = plan(tables, tickets, parameter)
    summary = (
        f"{collision_count} 组同间冲突，改号 {repair_count} 张后全卷通过目标唯一约束。"
        if repair_count <= parameter else f"需要改号 {repair_count} 张，预算 {parameter} 张；留待制签组处理。"
    )
    return {
        "summary": summary,
        "metrics": {"冲突组": collision_count, "需改号": repair_count, "通过试写": verified_count},
        "rows": [
            {"工票 ID": ticket.id, "工作间": ticket.workshop, "原票号": ticket.code, "目标票号": proposed, "动作": action}
            for ticket, proposed, action in planned
        ],
    }
