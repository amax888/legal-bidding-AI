# Load và tách văn bản từ file (PDF, DOCX, TXT, MD) hoặc từ URL PDF
import re
import io
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

def load_pdf_from_url(url: str) -> str:
    """Tải PDF từ URL và trích xuất text (tránh lưu file nặng trên máy)."""
    try:
        import requests
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(resp.content))
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
    """Liệt kê file hỗ trợ trong thư mục (không gồm urls.txt - dùng cho PDF từ URL)."""
    exts = {".txt", ".md", ".docx", ".pdf"}
    return [
        p for p in documents_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in exts and p.name != "urls.txt"
    ]

def list_document_urls(documents_dir: Path) -> List[str]:
    """Đọc danh sách URL PDF từ file urls.txt trong thư mục (mỗi dòng một URL)."""
    urls_file = documents_dir / "urls.txt"
    if not urls_file.is_file():
        return []
    lines = urls_file.read_text(encoding="utf-8", errors="replace").strip().splitlines()
    return [u.strip() for u in lines if u.strip() and not u.strip().startswith("#")]
