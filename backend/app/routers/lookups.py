from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.llm.base import LLMProvider
from app.llm.provider_factory import get_llm_provider
from app.models import Lookup
from app.schemas import LookupCreate, LookupList, LookupRead


router = APIRouter(prefix="/api/lookups", tags=["lookups"])


def build_lookup(text: str, explanation, provider: LLMProvider) -> Lookup:
    return Lookup(
        original=text,
        query_type=explanation.query_type,
        pronunciation=explanation.pronunciation,
        explanation=explanation.explanation,
        examples=[example.model_dump() for example in explanation.examples],
        model_provider=provider.name,
        model_name=provider.model_name,
        raw_response=explanation.raw_response,
    )


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

    lookup = build_lookup(text, explanation, provider)
    db.add(lookup)
    db.commit()
    db.refresh(lookup)
    return lookup


@router.get("", response_model=LookupList)
def list_lookups(
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None, max_length=120),
    query_type: str | None = Query(default=None, pattern="^(word|phrase|sentence)$"),
    db: Session = Depends(get_db),
) -> dict:
    statement = select(Lookup)
    if q and q.strip():
        statement = statement.where(Lookup.original.ilike(f"%{q.strip()}%"))
    if query_type:
        statement = statement.where(Lookup.query_type == query_type)
    statement = statement.order_by(Lookup.created_at.desc()).limit(limit).offset(offset)
    return {"items": db.scalars(statement).all()}


@router.get("/{lookup_id}", response_model=LookupRead)
def get_lookup(lookup_id: int, db: Session = Depends(get_db)) -> Lookup:
    lookup = db.get(Lookup, lookup_id)
    if lookup is None:
        raise HTTPException(status_code=404, detail="Lookup not found.")
    return lookup


@router.delete("/{lookup_id}", status_code=204)
def delete_lookup(lookup_id: int, db: Session = Depends(get_db)) -> None:
    lookup = db.get(Lookup, lookup_id)
    if lookup is None:
        raise HTTPException(status_code=404, detail="Lookup not found.")
    db.delete(lookup)
    db.commit()


@router.post("/{lookup_id}/regenerate", response_model=LookupRead)
async def regenerate_lookup(
    lookup_id: int,
    db: Session = Depends(get_db),
    provider: LLMProvider = Depends(get_llm_provider),
) -> Lookup:
    lookup = db.get(Lookup, lookup_id)
    if lookup is None:
        raise HTTPException(status_code=404, detail="Lookup not found.")

    try:
        explanation = await provider.explain(lookup.original)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    lookup.query_type = explanation.query_type
    lookup.pronunciation = explanation.pronunciation
    lookup.explanation = explanation.explanation
    lookup.examples = [example.model_dump() for example in explanation.examples]
    lookup.model_provider = provider.name
    lookup.model_name = provider.model_name
    lookup.raw_response = explanation.raw_response
    db.commit()
    db.refresh(lookup)
    return lookup
