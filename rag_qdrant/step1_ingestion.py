from pathlib import Path
from typing import Iterable, Tuple

class TextLoader:
    """
    SRP: Responsável somente por carregar conteúdo .txt do disco.
    Agora suporta diretórios organizados por seção/subseção/vídeo.
    """

    def iter_texts(self, base_path: str) -> Iterable[Tuple[str, str, dict]]:
        """
        Percorre recursivamente o diretório base e lê todos os .txt encontrados.
        Retorna (caminho_do_arquivo, conteúdo, metadados_extraídos).

        Exemplo de estrutura:
        data/
        ├── secao1/
        │   ├── subsecaoA/
        │   │   ├── video01.txt
        │   │   └── video02.txt
        │   └── subsecaoB/
        │       └── video03.txt
        """
        base = Path(base_path)
        for file in base.rglob("*.txt"):
            try:
                text = file.read_text(encoding="utf-8", errors="ignore")

                # Extração simples dos níveis de pasta
                rel = file.relative_to(base)
                parts = rel.parts[:-1]  # todas as pastas antes do arquivo
                meta = {
                    "section": parts[0] if len(parts) > 0 else None,
                    "topic_hint": parts[1] if len(parts) > 1 else None,
                    "video": file.stem
                }

                yield str(file), text, meta
            except Exception as e:
                print(f"⚠️ Erro ao ler {file}: {e}")
