from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException
from sqlalchemy import select

from src.config.resources import engine
from src.config.settings import JWT_SECRET
from src.models.users import users
from src.utils.passwords import matches


def login(username, password):
    with engine.connect() as db:
        user = db.execute(select(users).where(users.c.username == username)).mappings().first()
    stored = user["password_hash"] if user else f"{'0' * 32}:{'0' * 64}"
    if not matches(password, stored) or not user:
        raise HTTPException(401, "账号或口令错误")
    expires = datetime.now(timezone.utc) + timedelta(hours=8)
    token = jwt.encode({"sub": username, "role": user["role"], "exp": expires}, JWT_SECRET, algorithm="HS256")
    return {"token": token, "username": username, "role": user["role"]}
