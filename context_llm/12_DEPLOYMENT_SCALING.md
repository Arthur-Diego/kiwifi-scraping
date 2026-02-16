# Deploy e Escalabilidade (local → acesso de qualquer lugar)

## Meta
Começar rodando local no PC gamer e evoluir para acesso remoto com segurança.

---

## Opção A — Local only (MVP)
- Streamlit rodando na sua máquina
- Qdrant via Docker local
- Dados no filesystem Windows
- Vantagem: simples
- Risco: acesso somente na LAN

---

## Opção B — Acesso remoto rápido (curto prazo)
**Túnel seguro** para expor a UI local (com autenticação):
- Ex.: Cloudflare Tunnel / Tailscale / VPN
- Vantagem: você acessa do celular sem deploy completo
- Risco: precisa configurar segurança e limitar acesso

---

## Opção C — Arquitetura para produção (médio prazo)
Separar:
1) **Backend API** (FastAPI) com:
   - chat endpoint
   - campanhas endpoint
   - ingest/reindex endpoint
2) **Frontend**:
   - PWA (React/Next) OU Streamlit (se ficar suficiente)
3) **Infra**:
   - Qdrant (container)
   - armazenamento dos transcripts (volume)
   - banco de campanha (Postgres)

---

## Recomendação de trajetória
1) MVP local com Streamlit
2) Adicionar túnel seguro (para usar do smartphone)
3) Refatorar para FastAPI + Frontend (PWA) quando estabilizar features

---

## Considerações de performance
- Indexação pode ser pesada: rodar em job separado
- Cache de embeddings e respostas
- Persistir Qdrant em disco (volume)

---

## Configuração por ambiente
- `.env.local` (não commitar)
- `.env.prod`
- config via `pydantic-settings`

---

## Segurança (mínimo)
- senha/OTP no app ao expor remotamente
- nunca expor pasta inteira do Windows via web
- separar diretório “data” dedicado ao projeto
