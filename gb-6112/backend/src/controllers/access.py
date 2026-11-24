from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.config.settings import JWT_SECRET
from src.constants.roles import Role

bearer = HTTPBearer(auto_error=False)


def identity(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    if credentials is None:
        raise HTTPException(401, "请先登录")
    try:
        claims = jwt.decode(
            credentials.credentials, JWT_SECRET, algorithms=["HS256"], options={"require": ["exp", "sub", "role"]}
        )
        return {"username": claims["sub"], "role": Role(claims["role"])}
    except (jwt.InvalidTokenError, ValueError) as exc:
        raise HTTPException(401, "登录状态失效，请重新登录") from exc


def require_role(role):
    def authorize(user=Depends(identity)):
        if user["role"] != role:
            raise HTTPException(403, "当前账号没有此操作权限")
        return user

    return authorize


operator = require_role(Role.OPERATOR)
reviewer = require_role(Role.REVIEWER)
