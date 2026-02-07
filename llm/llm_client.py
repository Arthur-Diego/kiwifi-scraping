# llm/llm_client.py
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from dotenv import load_dotenv
import os

load_dotenv()


class LLMClient:
    """
    Encapsula chamadas ao modelo LLM da OpenAI via LangChain.
    Facilita integração com pipeline RAG (Qdrant + LLM).
    """

    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.7):
        self.api_key = os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("❌ Variável de ambiente OPENAI_API_KEY não definida no .env")

        # Inicializa o modelo da OpenAI via LangChain
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=self.api_key  # evita depender de variáveis globais
        )

    def generate(self, query: str, contexts: list[str]) -> str:
        """
        Gera uma resposta do LLM usando o contexto recuperado do Qdrant.
        """
        context_text = "\n\n".join(contexts)
        messages = [
            SystemMessage(content=(
                "Você é um assistente especializado em análise de métricas e geração de relatórios. "
                "Responda de forma objetiva e baseada no contexto fornecido."
            )),
            HumanMessage(content=f"Contexto:\n{context_text}\n\nPergunta:\n{query}")
        ]

        response = self.llm.invoke(messages)
        return response.content


# 🔍 Teste rápido (modo standalone)
if __name__ == "__main__":
    llm = LLMClient(model_name="gpt-4o-mini", temperature=0.6)
    mensagens = [
        SystemMessage(content="Você é um contador de histórias criativo."),
        HumanMessage(content="Conte uma história breve sobre O Senhor dos Anéis.")
    ]
    resposta = llm.llm.invoke(mensagens)
    print(resposta.content)
