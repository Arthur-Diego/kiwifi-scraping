from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from sentence_transformers import SentenceTransformer

from src.infrastructure.chunking.token_tools import TokenTools


@dataclass(frozen=True)
class SemanticChunkerConfig:
    target_tokens_per_chunk: int = 350
    max_tokens_per_chunk: int = 500
    overlap_tokens: int = 60
    max_tokens_per_file: int = 10_000
    similarity_break_threshold: float = 0.40


def _neighbor_cosine_similarity(vecs: np.ndarray) -> np.ndarray:
    vecs = np.asarray(vecs)
    n = vecs.shape[0]
    if n == 0:
        return np.asarray([], dtype=np.float32)

    sims = np.ones(n, dtype=np.float32)
    norms = np.linalg.norm(vecs, axis=1)
    for i in range(1, n):
        denom = norms[i] * norms[i - 1]
        sims[i] = float(np.dot(vecs[i], vecs[i - 1]) / denom) if denom else 0.0
    return sims


class SemanticChunker:
    """
    Legacy-style semantic chunking:
    - sentence boundaries
    - token-aware chunk limits
    - semantic break by neighbor similarity drops
    - large-file windowing
    """

    def __init__(
        self,
        *,
        embedder_model: str | None = None,
        embedder: SentenceTransformer | None = None,
        token_tools: TokenTools | None = None,
        cfg: SemanticChunkerConfig | None = None,
    ):
        if embedder is None and not embedder_model:
            raise ValueError("Provide either `embedder` or `embedder_model`.")

        self._embedder = embedder or SentenceTransformer(str(embedder_model))
        self._token_tools = token_tools or TokenTools()
        self._cfg = cfg or SemanticChunkerConfig()

    def chunk_text(
        self,
        text: str,
        *,
        chunk_size_chars: int,
        chunk_overlap_chars: int,
    ) -> list[str]:
        _ = chunk_size_chars
        _ = chunk_overlap_chars

        sentences = self._token_tools.split_sentences(text)
        if not sentences:
            return []

        total_tokens = self._token_tools.count_tokens(text)
        if total_tokens > self._cfg.max_tokens_per_file:
            return self._chunk_large_file(sentences)
        return self._chunk_sentences(sentences)

    def _chunk_large_file(self, sentences: list[str]) -> list[str]:
        chunks: list[str] = []
        window: list[str] = []
        window_tok = 0
        windows: list[str] = []

        for sentence in sentences:
            tok = self._token_tools.count_tokens(sentence)
            if window_tok + tok > self._cfg.max_tokens_per_file and window:
                windows.append(" ".join(window))
                window, window_tok = [], 0
            window.append(sentence)
            window_tok += tok

        if window:
            windows.append(" ".join(window))

        for chunk_window in windows:
            chunks.extend(self._chunk_sentences(self._token_tools.split_sentences(chunk_window)))
        return chunks

    def _chunk_sentences(self, sentences: list[str]) -> list[str]:
        if not sentences:
            return []

        tokens = self._token_tools.tokens_for_sentences(sentences)
        sent_vecs = self._embedder.encode(sentences, convert_to_numpy=True, normalize_embeddings=True)
        neighbor_sim = _neighbor_cosine_similarity(sent_vecs)

        chunks: list[str] = []
        buf: list[str] = []
        buf_tok = 0

        for idx, (sentence, tok) in enumerate(zip(sentences, tokens)):
            if buf and (buf_tok + tok > self._cfg.max_tokens_per_chunk):
                chunks.append(" ".join(buf).strip())
                buf = self._with_overlap(buf, self._cfg.overlap_tokens)
                buf_tok = self._token_tools.count_tokens(" ".join(buf)) if buf else 0

            if (
                buf
                and neighbor_sim[idx] < self._cfg.similarity_break_threshold
                and buf_tok >= self._cfg.target_tokens_per_chunk
            ):
                chunks.append(" ".join(buf).strip())
                buf = self._with_overlap(buf, self._cfg.overlap_tokens)
                buf_tok = self._token_tools.count_tokens(" ".join(buf)) if buf else 0

            buf.append(sentence)
            buf_tok += tok

        if buf:
            chunks.append(" ".join(buf).strip())

        return [item for item in chunks if item]

    def _with_overlap(self, buf: list[str], overlap_tokens: int) -> list[str]:
        if not buf or overlap_tokens <= 0:
            return []

        acc: list[str] = []
        tok = 0
        for sentence in reversed(buf):
            tok += self._token_tools.count_tokens(sentence)
            acc.append(sentence)
            if tok >= overlap_tokens:
                break
        return list(reversed(acc))

