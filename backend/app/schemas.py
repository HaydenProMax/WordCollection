from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


QueryType = Literal["word", "phrase", "sentence"]
Language = Literal["en", "zh"]


class ExampleSentence(BaseModel):
    english: str = Field(min_length=1)
    chinese: str = Field(min_length=1)


class LookupCreate(BaseModel):
    text: str = Field(min_length=1, max_length=1200)


class LookupUpdate(BaseModel):
    pronunciation: str | None = Field(default=None, max_length=500)
    explanation: str | None = Field(default=None, min_length=1, max_length=8000)
    examples: list[ExampleSentence] | None = None


class LookupExplanation(BaseModel):
    original: str = Field(min_length=1)
    source_language: Language = "en"
    target_language: Language = "zh"
    query_type: QueryType
    pronunciation: str = ""
    explanation: str = Field(min_length=1)
    examples: list[ExampleSentence] = Field(default_factory=list)
    raw_response: dict | None = None


class LookupRead(BaseModel):
    id: int
    original: str
    source_language: Language
    target_language: Language
    query_type: QueryType
    pronunciation: str
    explanation: str
    examples: list[ExampleSentence]
    model_provider: str
    model_name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LookupList(BaseModel):
    items: list[LookupRead]
