# Documento de Requisitos do Produto (PRD)

> Feature: `refactor_project_spec-driven`
> Entrada: `context_llm/PROMPT_ORGANIZACAO_PROJETO.md`

## Visao Geral

O repositorio `kiwifi-scraping` acumulou ambientes virtuais redundantes, artefatos de
build/runtime versionados indevidamente, dados de runtime no controle de versao,
arquivos criados por engano e documentacao sobreposta. Esse acumulo aumenta o tamanho
do repositorio, gera ruido em diffs, dificulta o onboarding e cria risco de vazamento de
dados sensiveis (ex.: bases locais e segredos). Paralelamente, a base de codigo backend em
`src/` ja adota uma organizacao em camadas (dominio, aplicacao, infraestrutura e interface)
que precisa ser confirmada, padronizada e protegida contra erosao.

Esta feature entrega um esforco de **higiene de repositorio + consolidacao estrutural do
backend**: define o que e essencial, o que deve ser ignorado pelo versionamento e o que pode
ser removido do disco, alem de consolidar a estrutura de camadas do backend de forma
consistente e documentada. O resultado e valioso porque reduz risco operacional e de
seguranca, acelera build/test/manutencao e estabelece uma estrutura previsivel para evolucoes
futuras, sem alterar comportamento funcional da aplicacao.

## Objetivos

- Reduzir o conteudo versionado ao essencial para build, execucao, teste e documentacao.
- Eliminar duplicidade de ambientes virtuais, consolidando um unico padrao.
- Garantir que dados de runtime e segredos nao estejam versionados, preservando dados reais
  por meio de backup previo.
- Consolidar documentacao sobreposta em uma fonte unica e navegavel.
- Confirmar e documentar a estrutura de camadas do backend, mantendo fronteiras claras entre
  transporte, aplicacao, dominio e infraestrutura.
- Sucesso medido por: (a) testes existentes continuam passando; (b) `main.py` e `run_app.sh`
  continuam importando e iniciando; (c) `git status` limpo de artefatos/dados; (d) ausencia de
  segredos e dados sensiveis no historico monitorado a partir desta entrega.

## Usuarios, consumidores e sistemas impactados

- **Desenvolvedores e mantenedores** do projeto: principais beneficiarios da estrutura limpa e
  previsivel.
- **Pipeline de execucao local**: scripts `run_app.sh`, `stop_app.sh`, `kill_streamlit.sh`,
  `reset_qdrant.sh` e `main.py`, que devem continuar funcionando.
- **Servicos de runtime consumidos pelo backend**: PostgreSQL (`postgres_data/`) e Qdrant
  (`qdrant_storage/`, `qdrant_snapshots/`), cujos dados reais devem ser preservados via backup.
- **Interface Streamlit** (`src/interface/streamlit_app`): consumidora do backend; tratada como
  dependente a ser preservada, sem alteracao de comportamento.
- **Fluxos principais**: clonar e configurar o ambiente; instalar dependencias; rodar testes;
  iniciar a aplicacao. **Casos de borda**: ambiente que ainda referencia venv antigo, dados de
  runtime previamente versionados e referencias ao nome antigo de `requeriments.txt`.

## Principais funcionalidades

1. **Auditoria e classificacao de itens do repositorio**
   - O que faz: inventaria raiz e subpastas e classifica cada item em MANTER, IGNORAR ou
     REMOVER, com justificativa de uma linha.
   - Por que e importante: cria base auditavel e aprovavel antes de qualquer alteracao.
   - Entradas/saidas: entrada = arvore atual do repositorio; saida = relatorio classificado.
   - RF1: O processo deve produzir uma lista classificada de todos os itens relevantes antes de
     qualquer remocao ou alteracao de versionamento.
   - RF2: O processo deve obter aprovacao explicita antes de remover do disco ou alterar
     versionamento.

2. **Consolidacao de ambiente virtual unico**
   - O que faz: define um unico padrao de ambiente virtual e marca os demais para remocao.
   - Por que e importante: elimina ambiguidade e reduz tamanho/ruido do repositorio.
   - Entradas/saidas: entrada = `.venv-linux/`, `.venv-wsl/`, `venv-project-kiwifi/`, `.pyenv/`;
     saida = um padrao definido e os demais marcados para remocao.
   - RF3: O resultado deve manter exatamente um padrao de ambiente virtual e remover os demais.
   - RF4: A escolha do padrao unico permanece em aberto neste PRD e sera confirmada antes da
     execucao (ver Premissas/Riscos).

3. **Saneamento de versionamento (ignorar artefatos e dados)**
   - O que faz: remove do versionamento artefatos e dados de runtime e garante que estejam no
     `.gitignore`.
   - Por que e importante: evita versionar caches, builds e dados sensiveis.
   - Entradas/saidas: entrada = `__pycache__/`, `.pytest_cache/`, `.idea/`, `*.Zone.Identifier`,
     `logs/`, `exports/`, `qdrant_storage/`, `qdrant_snapshots/`, `postgres_data/`, `data/*.db`,
     `.env`; saida = itens fora do versionamento e cobertos pelo `.gitignore`.
   - RF5: Artefatos e dados de runtime versionados indevidamente devem ser retirados do
     versionamento sem apagar o conteudo real do disco.
   - RF6: O `.gitignore` deve cobrir venvs, caches, builds, `.idea/`, `*.Zone.Identifier`, logs,
     exports, dados de runtime, `data/*.db` e `.env`.
   - RF7: O `.env` deve permanecer intocado e confirmado como ignorado pelo versionamento.

4. **Preservacao de dados de runtime via backup**
   - O que faz: garante backup dos dados reais antes de alterar versionamento ou remover itens.
   - Por que e importante: dados de runtime reais nao podem ser perdidos.
   - Entradas/saidas: entrada = `qdrant_storage/`, `qdrant_snapshots/`, `postgres_data/`,
     `data/*.db`, `exports/`, `logs/`; saida = backup confirmado antes de qualquer mudanca.
   - RF8: Antes de remover do versionamento ou do disco, os dados de runtime indicados devem ter
     backup confirmado.

5. **Remocao de itens obsoletos e criados por engano**
   - O que faz: remove do disco itens aprovados como REMOVER.
   - Por que e importante: elimina lixo que polui o repositorio.
   - Entradas/saidas: entrada = arquivo com caminho literal do Windows
     `C:\Users\arthu\.kiwifi-scraping\chat_history.db`, `backup_legacy/` e duplicados aprovados;
     saida = itens removidos do disco.
   - RF9: Apenas itens explicitamente aprovados como REMOVER podem ser apagados do disco.

6. **Consolidacao de documentacao**
   - O que faz: consolida documentacao sobreposta (`context/` vs `context_llm/`) em uma fonte
     unica, atualizando indices e links.
   - Por que e importante: reduz confusao e duplicidade documental.
   - Entradas/saidas: entrada = `context/` e `context_llm/`; saida = fonte consolidada com links
     validos.
   - RF10: A documentacao consolidada nao deve conter links quebrados apos a mudanca.

7. **Renomeacao de arquivo de dependencias**
   - O que faz: renomeia `requeriments.txt` para `requirements.txt` e atualiza referencias.
   - Por que e importante: corrige typo e alinha com convencao esperada por ferramentas.
   - Entradas/saidas: entrada = `requeriments.txt` e seus pontos de uso (scripts, Docker, docs);
     saida = `requirements.txt` com todas as referencias atualizadas.
   - RF11: Apos a renomeacao, nenhuma referencia ao nome antigo pode permanecer ativa em scripts,
     Docker ou documentacao.

8. **Confirmacao e padronizacao da estrutura de camadas do backend**
   - O que faz: confirma a organizacao em camadas existente em `src/` (dominio, aplicacao,
     infraestrutura, interface) e padroniza posicionamento de modulos sem alterar comportamento.
   - Por que e importante: protege as fronteiras do backend contra erosao e mantem previsibilidade.
   - Entradas/saidas: entrada = estrutura atual de `src/`; saida = estrutura confirmada e
     documentada, com inconsistencias de posicionamento apontadas.
   - RF12: A estrutura de camadas do backend deve ser documentada com evidencia do padrao
     predominante observado.
   - RF13: A reorganizacao estrutural deve preservar o comportamento atual da aplicacao (sem
     mudanca funcional).

9. **Verificacao de integridade pos-mudanca**
   - O que faz: valida que nada quebrou apos as alteracoes.
   - Por que e importante: garante que a higiene/reestruturacao nao introduziu regressao.
   - Entradas/saidas: entrada = suite de testes e pontos de entrada; saida = evidencia de
     execucao bem-sucedida.
   - RF14: Os testes existentes devem continuar passando apos as mudancas.
   - RF15: Os pontos de entrada (`main.py` e `run_app.sh`) devem continuar importando e iniciando.

## Contratos e dados de negocio

- **Dados obrigatorios a preservar**: dados reais de runtime (PostgreSQL, Qdrant, bases locais
  `data/*.db`, `exports/`) e o arquivo de segredos `.env`.
- **Dados opcionais/descartaveis**: caches, builds, arquivos `*.Zone.Identifier`, arquivo criado
  por engano com caminho literal do Windows e backups legados aprovados como REMOVER.
- **Validacoes de negocio**: nenhuma remocao ou alteracao de versionamento sem aprovacao previa;
  nenhum dado de runtime removido sem backup confirmado; `.env` nunca alterado.
- **Estados e transicoes relevantes**: cada item transita por classificado -> aprovado ->
  (ignorado | removido | renomeado | consolidado | mantido).
- **Retencao, privacidade, auditoria**: dados sensiveis e segredos saem do versionamento;
  backups dos dados de runtime sao retidos; cada lote de mudanca e registrado em commits
  pequenos e descritivos para rastreabilidade.

## Requisitos nao funcionais

- **Seguranca**: segredos (`.env`) e dados sensiveis nao podem permanecer versionados; nenhum
  segredo deve ser exposto em logs ou em saidas do processo.
- **Performance/operacao**: a limpeza deve reduzir o volume versionado sem degradar tempo de
  build, instalacao de dependencias ou inicializacao da aplicacao.
- **Resiliencia/recuperacao**: dados de runtime preservados por backup permitem recuperacao caso
  alguma remocao seja indevida; mudancas em lotes pequenos permitem reversao granular.
- **Observabilidade/auditoria**: cada etapa de mudanca deve deixar rastro (relatorio de
  classificacao, commits descritivos, evidencia de testes).
- **Compatibilidade**: pontos de entrada e scripts de execucao devem manter compatibilidade de
  uso apos renomeacoes e reorganizacoes (sem quebra de comando esperado).

## Requisitos operacionais e compliance

- **Retencao de dados**: backups dos dados de runtime retidos antes de qualquer remocao do
  versionamento ou do disco.
- **Dados sensiveis e privacidade**: `.env` e bases locais tratados como sensiveis; mantidos fora
  do versionamento.
- **Auditoria**: relatorio de auditoria/classificacao e historico de commits pequenos servem como
  trilha de mudancas.
- **Limites/protecao**: trabalho realizado em branch dedicado (`chore/organizacao-projeto`), sem
  push sem solicitacao explicita, e sem execucao antes de aprovacao do plano.
- **Suporte/troubleshooting**: entregavel final inclui `git status`, nova arvore de pastas e
  resumo do que foi removido, ignorado, consolidado e renomeado.

## Fora do escopo

- Escolha de padrao arquitetural (Clean Architecture vs MVC) e qualquer decisao tecnica de
  implementacao: pertencem a Tech Spec, nao a este PRD.
- Reescrita ou alteracao de comportamento funcional do backend; a reestruturacao e limitada a
  posicionamento/organizacao sem mudar funcionalidade.
- Qualquer trabalho de frontend/UI/UX da interface Streamlit alem de preserva-la como consumidor
  (sem redesenho visual, componentes ou interacoes).
- Limpeza ou reescrita do historico git ja existente (rewrite de commits passados).
- Migracoes de dados de PostgreSQL/Qdrant ou mudancas de schema.
- Definicao final do padrao unico de ambiente virtual, que sera confirmada antes da execucao.

---

### Premissas

- A estrutura em camadas observada em `src/` (`domain/`, `application/{ports,use_cases,services}`,
  `infrastructure/`, `interface/`) e o padrao predominante e deve ser preservada.
- Dados de runtime atualmente presentes contem dados reais que exigem backup previo.
- Os scripts de execucao e `main.py` representam os pontos de entrada oficiais.

### Dependencias externas

- Servicos de runtime PostgreSQL e Qdrant para validar que a aplicacao ainda inicia.
- Ferramenta de versionamento (git) para retirar itens do versionamento e registrar mudancas.

### Areas que exigem pesquisa/confirmacao

- Decisao do padrao unico de ambiente virtual (`.venv` vs `.pyenv` vs outro).
- Mapeamento completo das referencias a `requeriments.txt` (scripts, Docker, docs).
- Estrategia de consolidacao entre `context/` e `context_llm/`.

### Riscos de escopo

- Reestruturacao do backend pode crescer alem da higiene se nao for limitada a posicionamento.
- Remocao de dados de runtime sem backup adequado causaria perda irreversivel.
- Renomeacao de dependencias pode quebrar scripts/Docker se alguma referencia nao for atualizada.
