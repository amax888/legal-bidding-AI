# Vector store dùng FAISS (không cần build C++, có wheel trên Windows)
from pathlib import Path
import pickle
import numpy as np
from typing import List, Optional

from .loader import load_document, list_documents, list_document_urls, load_pdf_from_url
from .splitter import chunk_document, TextChunk
from .embedding import embed_texts, embed_query

try:
    import faiss
except ImportError:
    faiss = None

INDEX_FILE = "index.faiss"
META_FILE = "metadata.pkl"


def _index_path(persist_path: Path) -> Path:
    return persist_path / INDEX_FILE


def _meta_path(persist_path: Path) -> Path:
    return persist_path / META_FILE


def build_vector_store_from_documents(
    documents_dir: Path,
    persist_path: Path,
    chunk_size: int = 512,
    chunk_overlap: int = 128,
) -> int:
    """Đọc văn bản, chunk, embed và lưu bằng FAISS. Trả về số chunk."""
    if faiss is None:
        raise RuntimeError("Chưa cài đặt faiss-cpu. Chạy: pip install faiss-cpu")
    persist_path = Path(persist_path)
    persist_path.mkdir(parents=True, exist_ok=True)
    all_chunks: List[TextChunk] = []
    files = list_documents(documents_dir)
    for path in files:
        content = load_document(path)
        if not content.strip():
            continue
        chunks = chunk_document(
            content,
            source_name=path.name,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        all_chunks.extend(chunks)
    for url in list_document_urls(documents_dir):
        content = load_pdf_from_url(url)
        if not content.strip():
            continue
        source_name = url.split("/")[-1] if "/" in url else url
        chunks = chunk_document(
            content,
            source_name=source_name,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        all_chunks.extend(chunks)
    if not all_chunks:
        return 0
    texts = [c.content for c in all_chunks]
    metadatas = [{"source": c.source, "section": c.page_or_section or ""} for c in all_chunks]
    embeddings = embed_texts(texts)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings.astype(np.float32))
    faiss.write_index(index, str(_index_path(persist_path)))
    with open(_meta_path(persist_path), "wb") as f:
        pickle.dump({"documents": texts, "metadatas": metadatas}, f)
    return len(all_chunks)


def get_retriever(persist_path: Path, top_k: int = 5):
    """Trả về hàm retrieve(query, k?) -> list of {content, source, distance}."""

    def retrieve(query: str, k: Optional[int] = None) -> List[dict]:
        k = k or top_k
        if faiss is None:
            return []
        persist_path_p = Path(persist_path)
        if not _index_path(persist_path_p).exists() or not _meta_path(persist_path_p).exists():
            return []
        index = faiss.read_index(str(_index_path(persist_path_p)))
        with open(_meta_path(persist_path_p), "rb") as f:
            data = pickle.load(f)
        docs = data["documents"]
        metadatas = data["metadatas"]
        n = min(k, index.ntotal)
        if n <= 0:
            return []
        q_embedding = np.array([embed_query(query)], dtype=np.float32)
        distances, indices = index.search(q_embedding, n)
        out = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx < 0 or idx >= len(docs):
                continue
            meta = metadatas[idx] if idx < len(metadatas) else {}
            out.append({
                "content": docs[idx],
                "source": meta.get("source", ""),
                "distance": float(dist),
            })
        return out

    return retrieve
