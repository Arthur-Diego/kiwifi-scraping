from __future__ import annotations

import re


class TokenTools:
    """
    Utility compatible with legacy behavior:
    - sentence splitting
    - token counting
    """

    def __init__(self, encoding_name: str = "cl100k_base"):
        self._enc = None
        try:
            import tiktoken

            self._enc = tiktoken.get_encoding(encoding_name)
        except Exception:
            self._enc = None

    def split_sentences(self, text: str) -> list[str]:
        pieces = re.split(r"(?<=[\.\!\?])\s+", text.strip())
        return [piece.strip() for piece in pieces if piece.strip()]

    def count_tokens(self, text: str) -> int:
        if self._enc is not None:
            return len(self._enc.encode(text))
        # Fallback approximate tokenization when tiktoken is unavailable.
        return len(text.split())

    def tokens_for_sentences(self, sentences: list[str]) -> list[int]:
        return [self.count_tokens(item) for item in sentences]

