from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.domain.knowledge.entities import RetrievedContext

load_dotenv()


class LangChainOpenAIClient:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")
        self._api_key = api_key

    def generate_answer(
        self,
        *,
        query: str,
        contexts: list[RetrievedContext],
        model_name: str,
        temperature: float,
    ) -> str:
        llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=self._api_key,
        )

        context_lines = []
        for idx, ctx in enumerate(contexts, start=1):
            context_lines.append(
                f"[{idx}] {ctx.text}\nFonte: {ctx.source_path} (chunk {ctx.chunk_index})"
            )

        messages = [
            SystemMessage(
                content=(
                    "Voce e um assistente de Google Ads. Responda apenas com base no contexto recebido. "
                    "Se faltar evidencia, diga explicitamente. Estruture a resposta com: Resposta, Acoes sugeridas e Fontes."
                )
            ),
            HumanMessage(
                content=f"Contexto:\n\n" + "\n\n".join(context_lines) + f"\n\nPergunta:\n{query}")
        ]

        response = llm.invoke(messages)
        return str(response.content)
