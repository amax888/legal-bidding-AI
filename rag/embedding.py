# Embedding đa ngôn ngữ (hỗ trợ tiếng Việt) cho RAG
from typing import List
import numpy as np

_embedding_model = None

def get_embedding_model():
    """Lazy load model sentence-transformers (multilingual)."""
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        # Model hỗ trợ tiếng Việt tốt
        _embedding_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    return _embedding_model

def embed_texts(texts: List[str]) -> np.ndarray:
    """Embed danh sách đoạn văn bản."""
    if not texts:
        return np.array([]).reshape(0, 384)
    model = get_embedding_model()
    return model.encode(texts, show_progress_bar=len(texts) > 20)

def embed_query(query: str) -> List[float]:
    """Embed một câu truy vấn."""
    model = get_embedding_model()
    return model.encode([query], show_progress_bar=False)[0].tolist()
