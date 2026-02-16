# Arquitetura (SOLID + Clean Code)

## Objetivo
Organizar o projeto para:
- refatorar sem medo
- adicionar features (memória, YouTube, garimpagem) sem virar “bola de lama”
- permitir testes e isolamento de dependências (LLM, Qdrant, filesystem)

## Padrão recomendado
**Arquitetura em camadas + ports/adapters (hexagonal)**

### Camadas
1) **Domain** (regras do negócio)
2) **Application** (casos de uso)
3) **Infrastructure** (Qdrant, filesystem, LLM provider, transcrição)
4) **Interface** (Streamlit UI)

## Estrutura de pastas (sugestão)
```plaintext
src/
  domain/
    campaigns/
      entities.py
      value_objects.py
      services.py
    knowledge/
      entities.py
      policies.py
  application/
    use_cases/
      ingest_transcripts.py
      chat_with_knowledge.py
      record_campaign_event.py
      summarize_campaign.py
    ports/
      vector_store.py
      llm.py
      transcript_repo.py
      campaign_repo.py
      clock.py
  infrastructure/
    vectorstores/
      qdrant_store.py
    llm/
      openai_client.py   # ou outro provider
      local_model.py
    fs/
      windows_transcript_repo.py
    transcription/
      whisper_transcriber.py
    persistence/
      postgres_campaign_repo.py
      file_campaign_repo.py
  interface/
    streamlit_app/
      app.py
      components.py
tests/
```

## Interfaces (Ports) — exemplos
- `VectorStorePort`: upsert, query, delete, list_collections
- `LLMPort`: generate, embed
- `TranscriptRepositoryPort`: list_transcripts, read_transcript, compute_hash
- `CampaignRepositoryPort`: create_campaign, append_event, list_events

## Entidades do domínio (exemplos)
### Campaign
- id, name, created_at
- settings (geo, network, oferta, landing page)
- events (timeline)

### CampaignEvent
- timestamp
- kind: METRICS | DECISION | NOTE | RESULT
- payload (dict)
- tags (ex.: "keyword", "cpc", "ctr", "policy")

## Manifestos e versionamento
Criar um arquivo (ex.: `.index_manifest.json`) com:
- versão do splitter
- modelo de embedding
- transcript_version
- hash por arquivo
Isso permite reindexar com segurança.

## Testabilidade (regra)
- Application depende de ports (interfaces), nunca de infra direta.
- Infra implementa ports.
- UI chama casos de uso (application), não chama Qdrant direto.

## Padrões de qualidade
- Funções pequenas e nomeadas
- Sem “God classes”
- DTOs explícitos para inputs/outputs de use cases
- Tipagem com `pydantic` (opcional) para payloads de eventos e configs

## Onde colocar “LangChain”?
Recomendação:
- manter LangChain como detalhe de infraestrutura, não como o core do domínio.
- o domínio e os casos de uso não devem “saber” o que é LangChain.
