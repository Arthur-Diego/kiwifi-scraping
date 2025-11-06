import nltk
from typing import List
import tiktoken

# ✅ Garante que as dependências do NLTK estão disponíveis
for resource in ["punkt", "punkt_tab"]:
    try:
        nltk.data.find(f"tokenizers/{resource}")
    except LookupError:
        nltk.download(resource)

class TokenTools:
    """
    SRP: funcionalidades de tokenização e contagem de tokens.
    """
    def __init__(self, encoding_name: str = "cl100k_base"):
        # cl100k_base correlaciona bem com limites típicos de modelos modernos
        self.enc = tiktoken.get_encoding(encoding_name)

    def split_sentences(self, text: str) -> List[str]:
        # Segmentação robusta de sentenças (português e textos similares)
        return nltk.sent_tokenize(text)

    def count_tokens(self, text: str) -> int:
        return len(self.enc.encode(text))

    def tokens_for_sentences(self, sentences: List[str]) -> List[int]:
        return [self.count_tokens(s) for s in sentences]
