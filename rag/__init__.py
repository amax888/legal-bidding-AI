# RAG module - Retrieval-Augmented Generation cho văn bản pháp luật
from .store import get_retriever, build_vector_store_from_documents

__all__ = ["get_retriever", "build_vector_store_from_documents"]
