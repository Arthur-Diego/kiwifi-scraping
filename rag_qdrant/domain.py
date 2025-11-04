from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Chunk(BaseModel):
    id: str
    source: str
    chunk_index: int
    text: str
    token_count: int
    start_sentence: int
    end_sentence: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # Campos extras úteis para filtros
    date: Optional[str] = None
    section: Optional[str] = None
    topic_hint: Optional[str] = None  # (pode ser nulo: opcional)
