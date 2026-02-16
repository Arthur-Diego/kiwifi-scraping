from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class TranscriptDocument:
    source_path: str
    source_file: str
    text: str
    section: Optional[str] = None
    topic_hint: Optional[str] = None
    transcript_version: str = "v1"


@dataclass(frozen=True)
class KnowledgeChunk:
    chunk_id: str
    text: str
    source_path: str
    source_file: str
    chunk_index: int
    section: Optional[str] = None
    topic_hint: Optional[str] = None
    transcript_version: str = "v1"
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class RetrievedContext:
    text: str
    source_file: str
    source_path: str
    chunk_index: int
    section: Optional[str] = None
    topic_hint: Optional[str] = None
    score: Optional[float] = None


@dataclass(frozen=True)
class ChatAnswer:
    answer: str
    contexts: list[RetrievedContext]
