from typing import List, Iterable
from dataclasses import dataclass

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from .step2_tokenization import TokenTools
from .domain import Chunk
from .config import ChunkingConfig

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
        idx = 0
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
            chunks.extend(self._chunk_sentences(source, self.token_tools.split_sentences(w), date, section, topic_hint, starting_index=len(chunks)))
        return chunks

    def _chunk_sentences(self, source: str, sentences: List[str], date: str | None, section: str | None,
                         topic_hint: str | None, starting_index: int = 0) -> List[Chunk]:
        tokens = self.token_tools.tokens_for_sentences(sentences)
        # Embeddings por sentença para medir quedas de similaridade
        sent_vecs = self.embedder.encode(sentences)
        sim = cosine_similarity(sent_vecs, sent_vecs)  # matriz N x N (pode ser pesada, mas funciona para janelas moderadas)
        # Otimizamos usando tridiagonal: vizinhos próximos
        neighbor_sim = np.array([sim[i, i-1] if i > 0 else 1.0 for i in range(len(sentences))])

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
                buf, buf_tok, start_idx = self._with_overlap(buf, self.cfg.overlap_tokens), self.token_tools.count_tokens(" ".join(self._with_overlap(buf, self.cfg.overlap_tokens))), i

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
                buf, buf_tok, start_idx = self._with_overlap(buf, self.cfg.overlap_tokens), self.token_tools.count_tokens(" ".join(self._with_overlap(buf, self.cfg.overlap_tokens))), i

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
