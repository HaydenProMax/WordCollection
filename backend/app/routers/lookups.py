from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.llm.base import LLMProvider
from app.llm.provider_factory import get_llm_provider
from app.models import Lookup
from app.schemas import LookupCreate, LookupList, LookupRead


router = APIRouter(prefix="/api/lookups", tags=["lookups"])


@router.post("", response_model=LookupRead)
async def create_lookup(
    payload: LookupCreate,
    db: Session = Depends(get_db),
    provider: LLMProvider = Depends(get_llm_provider),
) -> Lookup:
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is required.")

    try:
        explanation = await provider.explain(text)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    lookup = Lookup(
        original=text,
        query_type=explanation.query_type,
        pronunciation=explanation.pronunciation,
        explanation=explanation.explanation,
        examples=[example.model_dump() for example in explanation.examples],
        model_provider=provider.name,
        model_name=provider.model_name,
        raw_response=explanation.raw_response,
    )
    db.add(lookup)
    db.commit()
    db.refresh(lookup)
    return lookup


@router.get("", response_model=LookupList)
def list_lookups(
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> dict:
    statement = select(Lookup).order_by(Lookup.created_at.desc()).limit(limit).offset(offset)
    return {"items": db.scalars(statement).all()}


@router.get("/{lookup_id}", response_model=LookupRead)
def get_lookup(lookup_id: int, db: Session = Depends(get_db)) -> Lookup:
    lookup = db.get(Lookup, lookup_id)
    if lookup is None:
        raise HTTPException(status_code=404, detail="Lookup not found.")
    return lookup
