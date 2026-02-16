# Segurança e Privacidade

## Dados sensíveis
- métricas de campanhas e performance
- possíveis informações de contas e pixels
- chaves de API (LLM provider)

## Regras
- Nunca commitar `.env`, chaves ou logs sensíveis
- Logs devem poder ser desligados ou anonimizados
- Se expor remotamente:
  - autenticação obrigatória
  - TLS sempre
  - limitar IPs quando possível

## Acesso aos arquivos (Windows)
- O app deve ler somente um diretório configurado (root do projeto), não o disco inteiro.
- Validar paths para evitar path traversal.

## Compliance (prático)
- Se usar YouTube/Google APIs: respeitar termos e limites
- Não automatizar ações que infrinjam políticas do Google Ads
