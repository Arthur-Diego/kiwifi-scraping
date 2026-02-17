from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str
    top_k: int = Field(default=8, ge=1, le=50)
    section: str | None = None
    model_name: str = "gpt-4o-mini"
    temperature: float = Field(default=0.7, ge=0.0, le=1.5)


class IngestRequest(BaseModel):
    input_paths: list[str]
    collection: str = "transcricoes"
    chunk_size_chars: int = 1200
    chunk_overlap_chars: int = 120


class ProductMiningListRequest(BaseModel):
    limit: int = Field(default=100, ge=1, le=1000)
    classification: str | None = None
    platform: str | None = None
