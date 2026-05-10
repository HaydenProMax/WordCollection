import pytest
from pydantic import ValidationError

from app.schemas import LookupCreate, LookupExplanation


def test_lookup_create_trims_in_route_but_validates_length() -> None:
    payload = LookupCreate(text=" subtle ")

    assert payload.text == " subtle "


def test_lookup_explanation_accepts_fixed_schema() -> None:
    explanation = LookupExplanation.model_validate(
        {
            "original": "subtle",
            "query_type": "word",
            "pronunciation": "/ˈsʌtəl/",
            "explanation": "微妙的、不易察觉的。",
            "examples": [
                {
                    "english": "There is a subtle difference.",
                    "chinese": "这里有一个细微差别。",
                }
            ],
        }
    )

    assert explanation.query_type == "word"
    assert explanation.examples[0].english == "There is a subtle difference."


def test_lookup_explanation_rejects_unknown_query_type() -> None:
    with pytest.raises(ValidationError):
        LookupExplanation.model_validate(
            {
                "original": "subtle",
                "query_type": "unknown",
                "explanation": "微妙的。",
                "examples": [],
            }
        )
