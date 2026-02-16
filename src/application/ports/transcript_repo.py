from __future__ import annotations

from typing import Iterable, Protocol

from src.domain.knowledge.entities import TranscriptDocument


class TranscriptRepositoryPort(Protocol):
    def iter_transcripts(self, input_paths: list[str]) -> Iterable[TranscriptDocument]:
        ...
