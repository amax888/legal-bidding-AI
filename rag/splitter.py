# Chia văn bản thành các chunk phù hợp cho embedding
import re
from typing import List
from dataclasses import dataclass

@dataclass
class TextChunk:
    content: str
    source: str
    page_or_section: str = ""

def split_by_sentences(text: str, max_chars: int = 512, overlap: int = 128) -> List[str]:
    """Tách văn bản thành các đoạn có độ dài gần max_chars, ưu tiên ranh giới câu."""
    if not text or not text.strip():
        return []
    # Chuẩn hóa: nhiều khoảng trắng -> 1, nhiều xuống dòng -> 2
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\n\s*\n", "\n\n", text.strip())
    sentences = re.split(r'(?<=[.!?])\s+|\n+', text)
    chunks = []
    current = []
    current_len = 0
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        add_len = len(s) + 1
        if current_len + add_len > max_chars and current:
            chunk = " ".join(current)
            chunks.append(chunk)
            # Overlap: giữ lại vài câu cuối
            overlap_len = 0
            overlap_sentences = []
            for x in reversed(current):
                overlap_sentences.insert(0, x)
                overlap_len += len(x) + 1
                if overlap_len >= overlap:
                    break
            current = overlap_sentences
            current_len = overlap_len
        current.append(s)
        current_len += add_len
    if current:
        chunks.append(" ".join(current))
    return chunks

def chunk_document(
    content: str,
    source_name: str,
    chunk_size: int = 512,
    chunk_overlap: int = 128,
) -> List[TextChunk]:
    """Chia nội dung văn bản thành các TextChunk."""
    raw_chunks = split_by_sentences(content, max_chars=chunk_size, overlap=chunk_overlap)
    return [
        TextChunk(content=c, source=source_name, page_or_section="")
        for c in raw_chunks
    ]
