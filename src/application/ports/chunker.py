from __future__ import annotations

from typing import Protocol


class ChunkerPort(Protocol):
    def chunk_text(
        self,
        text: str,
        *,
        chunk_size_chars: int,
        chunk_overlap_chars: int,
    ) -> list[str]:
        ...
