# API AI Trợ lý Pháp lý & Đấu thầu
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from config import settings
from rag.store import get_retriever, build_vector_store_from_documents
from rag.answer import generate_answer
from compliance.checker import (
    check_pccc_compliance,
    check_density_compliance,
    PCCCInput,
    DensityInput,
)

# Khởi tạo retriever khi chạy (có thể chưa có index)
_retriever = None

def _ensure_index():
    global _retriever
    if _retriever is None:
        try:
            n = build_vector_store_from_documents(
                settings.documents_dir,
                settings.vector_store_path,
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
            )
            _retriever = get_retriever(settings.vector_store_path, top_k=settings.top_k_retrieve)
        except Exception as e:
            raise RuntimeError(f"Không thể khởi tạo vector store: {e}")
    return _retriever

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: có thể pre-build index nếu cần
    try:
        _ensure_index()
    except Exception:
        pass
    yield
    # Shutdown
    pass

app = FastAPI(
    title="AI Trợ lý Pháp lý & Đấu thầu",
    description="RAG tra cứu văn bản pháp luật, TCVN; kiểm tra tuân thủ PCCC và mật độ xây dựng.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Request/Response models ---
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Câu hỏi tra cứu")

class ChatResponse(BaseModel):
    answer: str
    sources: list = []

class PCCCRequest(BaseModel):
    so_tang: int = Field(0, ge=0)
    chieu_cao_m: float = Field(0.0, ge=0)
    dien_tich_san_moi_tang_m2: float = Field(0.0, ge=0)
    so_loi_thoat: int = Field(1, ge=0)
    chieu_rong_loi_thoat_m: float = Field(1.0, ge=0)
    khoang_cach_xa_nhat_den_cua_thoat_m: float = Field(0.0, ge=0)
    co_sprinkler: bool = False
    loai_nha: str = "nhà ở"

class DensityRequest(BaseModel):
    dien_tich_lot_m2: float = Field(..., gt=0)
    dien_tich_xay_dung_m2: float = Field(0.0, ge=0)
    tong_dien_tich_san_m2: float = Field(0.0, ge=0)
    so_tang: int = Field(0, ge=0)

class ComplianceResponse(BaseModel):
    passed: bool
    message: str
    details: list
    references: list = []

# --- Routes ---
@app.get("/health")
def health():
    return {"status": "ok", "service": "legal-bidding-ai"}

@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Chat RAG: tra cứu văn bản và trả lời."""
    try:
        retriever = _ensure_index()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    docs = retriever(req.message, k=settings.top_k_retrieve)
    answer = generate_answer(
        req.message,
        docs,
        openai_api_key=settings.openai_api_key,
    )
    sources = [{"source": d.get("source"), "content": d.get("content", "")[:200]} for d in docs]
    return ChatResponse(answer=answer, sources=sources)

@app.post("/api/compliance/pccc", response_model=ComplianceResponse)
def compliance_pccc(req: PCCCRequest):
    """Kiểm tra tuân thủ PCCC theo thông số hồ sơ thiết kế."""
    try:
        retriever = _ensure_index()
    except RuntimeError:
        retriever = None
    inp = PCCCInput(
        so_tang=req.so_tang,
        chieu_cao_m=req.chieu_cao_m,
        dien_tich_san_moi_tang_m2=req.dien_tich_san_moi_tang_m2,
        so_loi_thoat=req.so_loi_thoat,
        chieu_rong_loi_thoat_m=req.chieu_rong_loi_thoat_m,
        khoang_cach_xa_nhat_den_cua_thoat_m=req.khoang_cach_xa_nhat_den_cua_thoat_m,
        co_sprinkler=req.co_sprinkler,
        loai_nha=req.loai_nha,
    )
    result = check_pccc_compliance(inp, retriever=retriever)
    return ComplianceResponse(
        passed=result.passed,
        message=result.message,
        details=result.details,
        references=result.references,
    )

@app.post("/api/compliance/density", response_model=ComplianceResponse)
def compliance_density(req: DensityRequest):
    """Kiểm tra mật độ xây dựng và FAR."""
    try:
        retriever = _ensure_index()
    except RuntimeError:
        retriever = None
    inp = DensityInput(
        dien_tich_lot_m2=req.dien_tich_lot_m2,
        dien_tich_xay_dung_m2=req.dien_tich_xay_dung_m2 or 0,
        tong_dien_tich_san_m2=req.tong_dien_tich_san_m2 or 0,
        so_tang=req.so_tang,
    )
    result = check_density_compliance(inp, retriever=retriever)
    return ComplianceResponse(
        passed=result.passed,
        message=result.message,
        details=result.details,
        references=result.references,
    )

@app.post("/api/ingest")
def ingest():
    """Xây lại vector store từ thư mục data/documents."""
    try:
        n = build_vector_store_from_documents(
            settings.documents_dir,
            settings.vector_store_path,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        global _retriever
        _retriever = get_retriever(settings.vector_store_path, top_k=settings.top_k_retrieve)
        return {"status": "ok", "chunks_indexed": n}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Giao diện web
static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/")
    def index():
        return FileResponse(static_dir / "index.html")
else:
    @app.get("/")
    def index():
        return {"message": "Chạy frontend từ thư mục static hoặc gọi API /api/chat, /api/compliance/pccc, /api/compliance/density"}
