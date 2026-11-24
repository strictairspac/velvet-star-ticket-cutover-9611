from pydantic import BaseModel, Field, field_validator

from src.utils.serial import canonical_json


class CaseInput(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=420)
    payload: dict

    @field_validator("title")
    @classmethod
    def check_title(cls, title):
        if len(title.strip()) < 2:
            raise ValueError("请输入至少两个字符的名称")
        return title.strip()

    @field_validator("payload")
    @classmethod
    def check_size(cls, payload):
        if len(canonical_json(payload)) > 750_000:
            raise ValueError("样本数据不能超过 750 KB")
        return payload


class CaseEntry(CaseInput):
    id: int
    code: str
    created_by: str
