# Vector store: dùng ChromaDB hoặc FAISS (FAISS không cần build C++ trên Windows)
import os
from pathlib import Path
from typing import List, Optional

from .loader import load_document, list_documents, list_document_urls, load_pdf_from_url
from .splitter import chunk_document, TextChunk
from .embedding import embed_texts, embed_query

# Tránh lỗi "Building wheel for chroma-hnswlib" trên Windows: mặc định dùng FAISS (không cần C++ Build Tools)
_USE_FAISS = os.environ.get("USE_FAISS", "1").strip().lower() in ("1", "true", "yes")

try:
    if not _USE_FAISS:
        import chromadb
        from chromadb.config import Settings as ChromaSettings
    else:
        chromadb = None
except Exception:
    chromadb = None

if chromadb is None:
    _USE_FAISS = True

COLLECTION_NAME = "legal_documents"


def build_vector_store_from_documents(
    documents_dir: Path,
    persist_path: Path,
    chunk_size: int = 512,
    chunk_overlap: int = 128,
) -> int:
    """Đọc văn bản, chunk, embed và lưu. Dùng FAISS nếu ChromaDB không dùng được."""
    if _USE_FAISS:
        from .store_faiss import build_vector_store_from_documents as _build_faiss
        return _build_faiss(documents_dir, persist_path, chunk_size, chunk_overlap)
    return _build_chroma(documents_dir, persist_path, chunk_size, chunk_overlap)


def _get_chroma_client(persist_path: Path):
    if chromadb is None:
        raise RuntimeError("ChromaDB chưa cài đặt. Trên Windows có thể dùng FAISS: set USE_FAISS=1 rồi pip install faiss-cpu")
    return chromadb.PersistentClient(
        path=str(persist_path),
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def _build_chroma(
    documents_dir: Path,
    persist_path: Path,
    chunk_size: int,
    chunk_overlap: int,
) -> int:
    client = _get_chroma_client(persist_path)
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Văn bản pháp luật, TCVN, định mức xây dựng"},
    )
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
    ids = [f"chunk_{i}" for i in range(len(all_chunks))]
    texts = [c.content for c in all_chunks]
    metadatas = [
        {"source": c.source, "section": c.page_or_section or ""}
        for c in all_chunks
    ]
    embeddings = embed_texts(texts)
    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings.tolist(),
        metadatas=metadatas,
    )
    return len(all_chunks)


def get_retriever(persist_path: Path, top_k: int = 5):
    """Trả về hàm retriever(query, k?) -> list of {content, source, distance}."""
    if _USE_FAISS:
        from .store_faiss import get_retriever as _get_faiss_retriever
        return _get_faiss_retriever(persist_path, top_k)

    def retrieve(query: str, k: Optional[int] = None) -> List[dict]:
        k = k or top_k
        client = _get_chroma_client(persist_path)
        collection = client.get_collection(COLLECTION_NAME)
        q_embedding = embed_query(query)
        results = collection.query(
            query_embeddings=[q_embedding],
            n_results=min(k, collection.count()),
            include=["documents", "metadatas", "distances"],
        )
        if not results["documents"] or not results["documents"][0]:
            return []
        out = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            out.append({
                "content": doc,
                "source": meta.get("source", ""),
                "distance": float(dist),
            })
        return out

    return retrieve
