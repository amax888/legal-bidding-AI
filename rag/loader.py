# Load và tách văn bản từ file (PDF, DOCX, TXT, MD)
import re
from pathlib import Path
from typing import List, Tuple

def load_text_file(path: Path) -> str:
    """Đọc file .txt hoặc .md."""
    return path.read_text(encoding="utf-8", errors="replace")

def load_docx(path: Path) -> str:
    """Đọc file .docx (chỉ text)."""
    try:
        from docx import Document
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception:
        return ""

def load_pdf(path: Path) -> str:
    """Đọc file PDF."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return ""

def load_document(path: Path) -> str:
    """Tự động chọn loader theo phần mở rộng."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in (".txt", ".md"):
        return load_text_file(path)
    if suffix == ".docx":
        return load_docx(path)
    if suffix == ".pdf":
        return load_pdf(path)
    return ""

def list_documents(documents_dir: Path) -> List[Path]:
    """Liệt kê file hỗ trợ trong thư mục."""
    exts = {".txt", ".md", ".docx", ".pdf"}
    return [p for p in documents_dir.rglob("*") if p.is_file() and p.suffix.lower() in exts]
