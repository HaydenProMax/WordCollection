import csv
import io
import json

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Lookup


router = APIRouter(prefix="/api/export", tags=["export"])


def list_all_lookups(db: Session) -> list[Lookup]:
    statement = select(Lookup).order_by(Lookup.created_at.desc())
    return list(db.scalars(statement).all())


@router.get("/json")
def export_json(db: Session = Depends(get_db)) -> Response:
    items = [
        {
            "id": lookup.id,
            "original": lookup.original,
            "query_type": lookup.query_type,
            "pronunciation": lookup.pronunciation,
            "explanation": lookup.explanation,
            "examples": lookup.examples,
            "model_provider": lookup.model_provider,
            "model_name": lookup.model_name,
            "created_at": lookup.created_at.isoformat(),
            "updated_at": lookup.updated_at.isoformat(),
        }
        for lookup in list_all_lookups(db)
    ]
    body = json.dumps({"items": items}, ensure_ascii=False, indent=2)
    return Response(
        content=body,
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="encollect-lookups.json"'},
    )


@router.get("/csv")
def export_csv(db: Session = Depends(get_db)) -> Response:
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "id",
            "original",
            "query_type",
            "pronunciation",
            "explanation",
            "examples",
            "model_provider",
            "model_name",
            "created_at",
            "updated_at",
        ],
    )
    writer.writeheader()
    for lookup in list_all_lookups(db):
        writer.writerow(
            {
                "id": lookup.id,
                "original": lookup.original,
                "query_type": lookup.query_type,
                "pronunciation": lookup.pronunciation,
                "explanation": lookup.explanation,
                "examples": json.dumps(lookup.examples, ensure_ascii=False),
                "model_provider": lookup.model_provider,
                "model_name": lookup.model_name,
                "created_at": lookup.created_at.isoformat(),
                "updated_at": lookup.updated_at.isoformat(),
            }
        )

    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="encollect-lookups.csv"'},
    )
