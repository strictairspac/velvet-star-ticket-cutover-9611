from fastapi import APIRouter
from src.schemas.auth import Login, Session
from src.services.auth import login

router = APIRouter(prefix="/auth", tags=["Session"])


@router.post("/login", response_model=Session)
def authenticate(form: Login):
    return login(form.username, form.password)
