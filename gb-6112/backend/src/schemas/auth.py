from pydantic import BaseModel, Field
from src.constants.roles import Role


class Login(BaseModel):
    username: str = Field(min_length=1, max_length=48)
    password: str = Field(min_length=1, max_length=160)


class Session(BaseModel):
    token: str
    username: str
    role: Role
