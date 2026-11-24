from fastapi import APIRouter, Depends, HTTPException, Query

from src.config.resources import engine
from src.controllers.access import identity, operator
from src.controllers.workbench import publish_case, register_supplementation
from src.domain.scenario import CONFIG
from src.schemas.tickets import (
    LedgerEntry, PublicationEntry, PublicationSummary, PublishInput, SupplementEntry, SupplementInput,
)
from src.services import tickets

router = APIRouter(tags=["Tickets"])


@router.get("/cases/{case_id}/supplements", response_model=list[SupplementEntry], dependencies=[Depends(identity)])
def list_supplements(case_id: int):
    with engine.connect() as db:
        if tickets.load_case(db, case_id) is None:
            raise HTTPException(404, "资料不存在")
        return tickets.supplements(db, case_id)


@router.post("/cases/{case_id}/supplements", response_model=list[SupplementEntry], status_code=201)
def register(case_id: int, form: SupplementInput, user=Depends(operator)):
    return register_supplementation(case_id, form, user)


@router.get("/publications", response_model=list[PublicationSummary], dependencies=[Depends(identity)])
def publication_list():
    with engine.connect() as db:
        return tickets.publications(db)


@router.get("/cases/{case_id}/publication", response_model=PublicationEntry | None, dependencies=[Depends(identity)])
def publication_detail(case_id: int):
    with engine.connect() as db:
        if tickets.load_case(db, case_id) is None:
            raise HTTPException(404, "资料不存在")
        entry = tickets.publication(db, case_id)
        if entry is None:
            return None
        return {**entry, "issues": tickets.issues(db, case_id)}


@router.post("/cases/{case_id}/publication", response_model=PublicationEntry, status_code=201)
def publish(case_id: int, form: PublishInput, user=Depends(operator)):
    if form.parameter > CONFIG["max_parameter"]:
        raise HTTPException(422, f"参数不能超过 {CONFIG['max_parameter']}")
    return publish_case(case_id, form.parameter, user)


@router.get("/tickets/{ticket_id}", response_model=list[LedgerEntry], dependencies=[Depends(identity)])
def ticket_history(ticket_id: str):
    if tickets.normalise_ticket_id(ticket_id) is None:
        raise HTTPException(422, "工票 ID 仅接受 1 到 16 位大写字母或数字")
    with engine.connect() as db:
        return tickets.ledger(db, ticket_id=ticket_id)


@router.get("/tickets", response_model=list[LedgerEntry], dependencies=[Depends(identity)])
def ticket_search(workshop: str = Query(min_length=1, max_length=32), code: str = Query(min_length=1, max_length=60)):
    with engine.connect() as db:
        return tickets.ledger(db, workshop=workshop, code=code)
