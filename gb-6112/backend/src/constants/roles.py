from enum import StrEnum


class Role(StrEnum):
    OPERATOR = "operator"
    REVIEWER = "reviewer"
    VIEWER = "viewer"
