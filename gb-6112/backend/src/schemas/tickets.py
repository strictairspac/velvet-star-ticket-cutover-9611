from pydantic import BaseModel, Field, field_validator

from src.domain.tickets import ID


class TicketInput(BaseModel):
    id: str = Field(min_length=1, max_length=16)
    workshop: str = Field(min_length=1, max_length=32)
    code: str = Field(min_length=1, max_length=60)
    serial: int = Field(strict=True, ge=1, le=1_000_000)

    @field_validator("id")
    @classmethod
    def check_id(cls, value):
        if not ID.fullmatch(value):
            raise ValueError("工票 ID 仅接受 1 到 16 位大写字母或数字")
        return value

    @field_validator("workshop", "code")
    @classmethod
    def check_text(cls, value):
        if not value.strip():
            raise ValueError("工作间和票号须含可见字符")
        if any(ord(char) < 32 or 0xD800 <= ord(char) <= 0xDFFF for char in value):
            raise ValueError("工作间和票号不可包含控制字符或孤立代理字符")
        return value


class SupplementInput(BaseModel):
    tickets: list[TicketInput] = Field(min_length=1, max_length=250)


class SupplementEntry(BaseModel):
    case_id: int
    ticket_id: str
    workshop: str
    code: str
    serial: int
    created_at: int


class IssueEntry(BaseModel):
    case_id: int
    ticket_id: str
    workshop: str
    old_code: str
    new_code: str
    serial: int
    action: str
    issued_at: int


class PublicationSummary(BaseModel):
    case_id: int
    actor: str
    published_at: int
    parameter: int
    ticket_count: int
    collision_count: int
    changed_count: int
    verified_count: int
    digest: str


class PublicationEntry(PublicationSummary):
    issues: list[IssueEntry]


class LedgerEntry(BaseModel):
    case_id: int
    case_code: str
    case_title: str
    ticket_id: str
    workshop: str
    old_code: str
    serial: int
    new_code: str | None
    action: str | None
    issued_at: int | None
    published: bool


class PublishInput(BaseModel):
    parameter: int = Field(strict=True, ge=1)
