# guidelines.md

- Padroes de codigo detectados:
- Uso de classes para servicos e repositorios.
- Separacao em camadas (controller, facade, service, repository, ui).
- Uso de `dataclass` para configuracao e `pydantic` para modelos de dominio.
- Uso de `argparse` em CLIs (ex.: `rag_qdrant/main.py`).

- Convencoes de naming:
- Modulos e funcoes em `snake_case`.
- Classes em `PascalCase`.
- Excecao detectada: classe `extractor_facade` em lowercase.

- Padroes de testes:
- nao identificado

- Praticas recorrentes no repo:
- Blocos `if __name__ == "__main__"` para execucao local.
- Logs via `print`.
- Uso de `sys.path.append` em apps Streamlit para importar modulos do repo.
