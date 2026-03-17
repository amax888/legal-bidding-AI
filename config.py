# Cấu hình ứng dụng AI Trợ lý Pháp lý & Đấu thầu
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    # Đường dẫn thư mục văn bản và vector store
    documents_dir: Path = BASE_DIR / "data" / "documents"
    vector_store_path: Path = BASE_DIR / "data" / "chroma_db"
    
    # RAG
    chunk_size: int = 512
    chunk_overlap: int = 128
    top_k_retrieve: int = 5
    
    # OpenAI (tùy chọn - để trống thì dùng trả lời từ ngữ cảnh thuần)
    openai_api_key: str = ""
    
    # Bảo vệ /api/ingest trên production: đặt key trong .env, gọi kèm header X-API-Key
    ingest_api_key: str = ""
    
    model_config = {"env_file": ".env", "extra": "ignore"}

settings = Settings()
# Tạo thư mục nếu chưa có
settings.documents_dir.mkdir(parents=True, exist_ok=True)
settings.vector_store_path.mkdir(parents=True, exist_ok=True)
