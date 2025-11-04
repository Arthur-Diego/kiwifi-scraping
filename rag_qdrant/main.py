import argparse
from pathlib import Path
from typing import List

from .config import ChunkingConfig, EmbeddingConfig, QdrantConfig, Paths
from .ingestion import TextLoader
from .tokenization import TokenTools
from .chunker import SemanticChunker
from .embeddings import SentenceEmbedder
from .exporter import ChunkExporter
from .qdrant_writer import QdrantRepository


def run_pipeline(
    inputs: List[str],
    export_filename: str,
    qdrant_collection: str,
    date: str | None,
    section: str | None
) -> None:
    """
    Executa o pipeline completo de ingestão, chunkificação, exportação e inserção no Qdrant.
    Agora suporta diretórios hierárquicos (seção/subseção/vídeo).
    """

    # === Injeção de dependências ===
    token_tools = TokenTools()
    emb_cfg = EmbeddingConfig()
    embedder = SentenceEmbedder(emb_cfg.model_name)
    chunker = SemanticChunker(token_tools=token_tools, embedder=embedder, cfg=ChunkingConfig())
    exporter = ChunkExporter()
    qdrant_repo = QdrantRepository(QdrantConfig(collection=qdrant_collection), embedder)

    loader = TextLoader()
    all_chunks = []

    # =====================================================
    # 🔧 ALTERAÇÃO: suporte a diretórios recursivos e metadados
    # =====================================================
    for path in inputs:
        p = Path(path)

        if p.is_dir():
            # Percorre diretório completo (seções, subseções, vídeos)
            for source, text, meta in loader.iter_texts(str(p)):
                chunks = chunker.chunk_text(
                    source=source,
                    text=text,
                    date=date,
                    section=meta.get("section")
                )
                all_chunks.extend(chunks)

        else:
            # Compatibilidade com lista de arquivos individuais
            parent_dir = str(p.parent)
            for source, text, meta in loader.iter_texts(parent_dir):
                if source == str(p):
                    chunks = chunker.chunk_text(
                        source=source,
                        text=text,
                        date=date,
                        section=meta.get("section")
                    )
                    all_chunks.extend(chunks)
    # =====================================================
    # 🔧 FIM DAS ALTERAÇÕES
    # =====================================================

    # Exporta para JSONL (performático)
    out_path = exporter.to_jsonl(all_chunks, export_filename)
    print(f"✅ Chunks exportados → {out_path} (total: {len(all_chunks)})")

    # Insere no Qdrant
    qdrant_repo.upsert_chunks(all_chunks, batch_size=128)
    print(f"✅ Inseridos {len(all_chunks)} chunks na coleção '{qdrant_collection}'.")


def build_argparser() -> argparse.ArgumentParser:
    """
    Constrói o parser de argumentos da linha de comando.
    """
    p = argparse.ArgumentParser(description="Pipeline de chunk semântico + inserção em Qdrant")
    p.add_argument(
        "--inputs",
        nargs="+",
        required=True,
        help="Diretório base ou arquivos .txt (ex: data/ ou data/**/*.txt)"
    )
    p.add_argument(
        "--export",
        default="chunks.jsonl",
        help="Nome do arquivo de exportação JSONL (padrão: chunks.jsonl)"
    )
    p.add_argument(
        "--collection",
        default="transcricoes",
        help="Nome da coleção Qdrant (padrão: transcricoes)"
    )
    p.add_argument(
        "--date",
        default=None,
        help="Metadado opcional de data (ISO, ex: 2025-11-04)"
    )
    p.add_argument(
        "--section",
        default=None,
        help="Metadado opcional de seção (ex: secao1)"
    )
    return p


if __name__ == "__main__":
    args = build_argparser().parse_args()
    run_pipeline(
        inputs=args.inputs,
        export_filename=args.export,
        qdrant_collection=args.collection,
        date=args.date,
        section=args.section
    )
    