from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

class SentenceEmbedder:
    """
    SRP: gerar embeddings. Livre (HF), eficaz e replicável.
    """
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)

    @property
    def dim(self) -> int:
        # Descobre a dimensionalidade do modelo
        v = self.encode(["teste"])
        return v.shape[1]

    def encode(self, texts: List[str]) -> np.ndarray:
        # Retorna np.ndarray [N, D]
        embs = self.model.encode(texts, batch_size=64, convert_to_numpy=True, normalize_embeddings=True)
        return np.asarray(embs, dtype=np.float32)
