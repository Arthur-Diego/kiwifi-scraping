from typing import List
from dataclasses import dataclass

import numpy as np

from .step2_tokenization import TokenTools
from .domain import Chunk
from .config import ChunkingConfig


def _neighbor_cosine_similarity(vecs: np.ndarray) -> np.ndarray:
    """
    Similaridade do cosseno entre vizinhos consecutivos (i-1, i).

    Evita criar matriz NxN (muito cara) só para olhar vizinhos.
    Retorna um array onde sim[0] = 1.0 por convenção.
    """
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


@dataclass
class SemanticChunker:
    """
    SRP: quebrar texto em chunks SEM quebrar frases e respeitando coerência.
    Usa dois sinais:
      (1) limite por tokens, (2) quedas de similaridade semântica entre sentenças.
    """
    token_tools: TokenTools
    embedder: "SentenceEmbedder"  # type: ignore
    cfg: ChunkingConfig

    def chunk_text(self, source: str, text: str, date: str | None = None, section: str | None = None,
                   topic_hint: str | None = None) -> List[Chunk]:
        sentences = self.token_tools.split_sentences(text)
        if not sentences:
            return []

        # 1) Se o arquivo todo excede o limite global, processamos em "macro-janelas"
        total_tokens = self.token_tools.count_tokens(text)
        if total_tokens > self.cfg.max_tokens_per_file:
            # Construir janelas de ~max_tokens_per_file sem quebrar frases
            return self._chunk_large_file(source, sentences, date, section, topic_hint)

        # 2) Chunkificação normal
        return self._chunk_sentences(source, sentences, date, section, topic_hint)

    def _chunk_large_file(self, source: str, sentences: List[str], date: str | None, section: str | None,
                          topic_hint: str | None) -> List[Chunk]:
        """
        Divide o arquivo em janelas (sem quebrar frases) de até max_tokens_per_file,
        e em seguida, cada janela passa pelo mesmo processo semântico fino.
        """
        chunks: List[Chunk] = []
        current: List[str] = []
        current_tok = 0
        window_chunks: List[str] = []

        for s in sentences:
            t = self.token_tools.count_tokens(s)
            if current_tok + t > self.cfg.max_tokens_per_file and current:
                window_chunks.append(" ".join(current))
                current, current_tok = [], 0
            current.append(s)
            current_tok += t

        if current:
            window_chunks.append(" ".join(current))

        # Agora refina cada janela com o método semântico fino
        for w in window_chunks:
            chunks.extend(
                self._chunk_sentences(
                    source,
                    self.token_tools.split_sentences(w),
                    date,
                    section,
                    topic_hint,
                    starting_index=len(chunks),
                )
            )
        return chunks

    def _chunk_sentences(self, source: str, sentences: List[str], date: str | None, section: str | None,
                         topic_hint: str | None, starting_index: int = 0) -> List[Chunk]:
        tokens = self.token_tools.tokens_for_sentences(sentences)
        # Embeddings por sentença para medir quedas de similaridade
        sent_vecs = self.embedder.encode(sentences)
        neighbor_sim = _neighbor_cosine_similarity(sent_vecs)

        chunks: List[Chunk] = []
        buf: List[str] = []
        buf_tok = 0
        start_idx = 0
        chunk_idx = starting_index

        for i, (s, tok) in enumerate(zip(sentences, tokens)):
            # Se exceder o teto duro, fecha antes de adicionar
            if buf and (buf_tok + tok > self.cfg.max_tokens_per_chunk):
                text = " ".join(buf)
                chunks.append(Chunk(
                    id=f"{source}::chunk_{chunk_idx:06d}",
                    source=source,
                    chunk_index=chunk_idx,
                    text=text,
                    token_count=self.token_tools.count_tokens(text),
                    start_sentence=start_idx,
                    end_sentence=i-1,
                    date=date, section=section, topic_hint=topic_hint
                ))
                chunk_idx += 1

                # inicia próximo buffer com sobreposição
                buf = self._with_overlap(buf, self.cfg.overlap_tokens)
                buf_tok = self.token_tools.count_tokens(" ".join(buf)) if buf else 0
                start_idx = i

            # Critério semântico: queda de similaridade
            if buf and neighbor_sim[i] < self.cfg.similarity_break_threshold and buf_tok >= self.cfg.target_tokens_per_chunk:
                text = " ".join(buf)
                chunks.append(Chunk(
                    id=f"{source}::chunk_{chunk_idx:06d}",
                    source=source,
                    chunk_index=chunk_idx,
                    text=text,
                    token_count=self.token_tools.count_tokens(text),
                    start_sentence=start_idx,
                    end_sentence=i-1,
                    date=date, section=section, topic_hint=topic_hint
                ))
                chunk_idx += 1
                buf = self._with_overlap(buf, self.cfg.overlap_tokens)
                buf_tok = self.token_tools.count_tokens(" ".join(buf)) if buf else 0
                start_idx = i

            # adiciona a sentença
            buf.append(s)
            buf_tok += tok

        # último chunk (restante)
        if buf:
            text = " ".join(buf)
            chunks.append(Chunk(
                id=f"{source}::chunk_{chunk_idx:06d}",
                source=source,
                chunk_index=chunk_idx,
                text=text,
                token_count=self.token_tools.count_tokens(text),
                start_sentence=start_idx,
                end_sentence=len(sentences)-1,
                date=date, section=section, topic_hint=topic_hint
            ))

        return chunks

    def _with_overlap(self, buf: List[str], overlap_tokens: int) -> List[str]:
        """
        Mantém uma sobreposição aproximada em tokens a partir do fim do buffer atual.
        Garante coerência entre chunks vizinhos.
        """
        if not buf or overlap_tokens <= 0:
            return []

        # Reconstitui do fim até alcançar ~overlap_tokens
        acc: List[str] = []
        tok = 0
        for s in reversed(buf):
            tok += self.token_tools.count_tokens(s)
            acc.append(s)
            if tok >= overlap_tokens:
                break
        return list(reversed(acc))
