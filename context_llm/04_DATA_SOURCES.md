# Fontes de Dados (Vídeos e Transcrições)

## Origem
- Vídeos baixados de uma plataforma (Kiwify)
- Conteúdo: Google Ads + venda em plataformas estrangeiras (ClickBank, Digistore24, Buygoods, MaxWeb, etc.)
- Os vídeos e transcrições estão no **Windows**, organizados em **seções e subseções**.

## Desafio principal
- Muitos vídeos importantes são “tirar dúvidas/mentoria” e não têm títulos descritivos.
- Você precisa recuperar o conteúdo por **busca semântica** e por sinais internos do texto.

## Recomendação de organização (não obrigatória, mas ajuda)
### Estrutura de pastas
- `Videos/<secao>/<subsecao>/<arquivo>.mp4`
- `Transcripts/<secao>/<subsecao>/<arquivo>.txt` (ou `.srt`, `.vtt`, `.json`)

### Convenção de metadados
Para cada transcript, capturar e guardar:
- `source_path`: caminho completo no Windows
- `section`, `subsection`
- `title_guess`: (opcional) título inferido via LLM a partir de resumo curto
- `content_type`: aula / dúvida / mentoria / case
- `created_at`: data do arquivo (se útil)
- `language`: pt-BR (provável)

## Qualidade da transcrição
Você mencionou incerteza na acurácia do modelo usado.
### Estratégia recomendada:
- **V1**: usar transcrições existentes para ter valor rapidamente.
- **V2**: reprocessar gradualmente:
  - escolher modelo com boa acurácia em pt-BR
  - gerar timestamps (ideal)
  - (opcional) diarização (se for útil)
- Adotar versionamento:
  - `transcript_version`: v1, v2, ...
  - indexar por versão para comparar qualidade

## Timestamps
Se você tiver SRT/VTT:
- excelente para citações “no tempo” e para abrir o trecho no vídeo.
Se não tiver:
- manter `chunk_index` e `char_start/char_end` + “melhor esforço”.

## Importante (para RAG profissional)
- Armazenar chunk com:
  - texto
  - metadados (pasta, arquivo, seção)
  - (se tiver) timestamp início/fim
  - hash do conteúdo (para evitar duplicatas)
