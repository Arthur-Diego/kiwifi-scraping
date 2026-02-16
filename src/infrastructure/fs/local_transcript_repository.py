from __future__ import annotations

from pathlib import Path
from typing import Iterable

from src.domain.knowledge.entities import TranscriptDocument


class LocalTranscriptRepository:
    """Filesystem adapter for transcript loading (recursive .txt discovery)."""

    def iter_transcripts(self, input_paths: list[str]) -> Iterable[TranscriptDocument]:
        for input_path in input_paths:
            path = Path(input_path)
            if path.is_file() and path.suffix.lower() == ".txt":
                yield self._read_single_file(path, base=path.parent)
                continue

            if path.is_dir():
                for file_path in path.rglob("*.txt"):
                    yield self._read_single_file(file_path, base=path)

    def _read_single_file(self, file_path: Path, *, base: Path) -> TranscriptDocument:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        rel_parts = file_path.relative_to(base).parts
        section = rel_parts[0] if len(rel_parts) > 1 else None
        topic_hint = rel_parts[1] if len(rel_parts) > 2 else None
        return TranscriptDocument(
            source_path=str(file_path),
            source_file=file_path.name,
            text=text,
            section=section,
            topic_hint=topic_hint,
        )
