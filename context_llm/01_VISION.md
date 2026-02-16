# Visão do Projeto

## Nome (provisório)
**Campaign Copilot (RAG)** — Assistente local para orientar decisões de campanhas no Google Ads, usando conhecimento extraído de transcrições de vídeos e memória de campanhas.

## Problema
Você possui uma biblioteca de vídeos (Kiwify) sobre:
- Google Ads (estrutura, otimização, decisões)
- Venda de produtos online em plataformas estrangeiras (ClickBank, Digistore24, Buygoods, MaxWeb etc.)

Boa parte não foi assistida. Os vídeos de **tirar dúvidas** são os mais valiosos, porém:
- nem sempre têm título/assunto descritivo
- o conteúdo real é desconhecido até ser consumido
- buscar manualmente é lento

## Objetivo
Criar um sistema tipo **ChatGPT** que:
1) permita **pesquisar e conversar** com o conteúdo dos vídeos (RAG com fontes);
2) funcione como **assistente de campanha**, recebendo métricas e contexto do seu Google Ads;
3) mantenha uma **memória cronológica** por campanha (o que foi feito, por quê, resultados);
4) gere **orientações acionáveis** (o que mudar agora, o próximo passo, o que monitorar).

## Princípios
- **Precisão > fluidez**: preferir respostas com evidências (citações dos trechos).
- **Rastreabilidade**: toda orientação deve ser justificável (fonte + raciocínio).
- **Separação de responsabilidades**: SOLID, Clean Code, componentes isolados.
- **Evolutivo**: começar local e escalar para acesso remoto (smartphone).
- **Observável**: logs de perguntas, documentos recuperados e decisões do sistema.

## Não-objetivos (por enquanto)
- Treinar/fine-tunar modelo próprio
- Baixar mais vídeos (o acervo principal já está local)
- Automação “hands-off” que execute alterações na conta (foco em **assistir** e orientar)

## Resultado esperado (definição de sucesso)
- Você consegue responder dúvidas e tomar decisões de otimização com base em:
  - trechos relevantes das transcrições
  - histórico cronológico da campanha
- Reduzir tempo gasto “procurando vídeo” e “tentando lembrar o que o mentor falou”.
- Aumentar consistência e velocidade de iteração na campanha (testes, ajustes, learnings).

## Glossário rápido
- **RAG**: Retrieval-Augmented Generation (recupera trechos + gera resposta).
- **Chunk**: pedaço de texto indexado (janela do transcript).
- **Memória de campanha**: timeline com métricas, decisões e resultados.
