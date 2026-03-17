# AI Trợ lý Pháp lý & Đấu thầu (Legal & Bidding AI)

Ứng dụng RAG (Retrieval-Augmented Generation) cho ngành xây dựng tại Việt Nam: tra cứu nhanh văn bản quy phạm pháp luật, tiêu chuẩn TCVN, định mức; tự động kiểm tra tuân thủ PCCC và mật độ xây dựng.

## Chức năng

- **Chat RAG**: Hỏi đáp tra cứu thông tư, nghị định về quản lý chi phí, hợp đồng, quy chuẩn thiết kế (PCCC, mật độ). Dữ liệu mẫu gồm trích yếu QCVN 06 (PCCC), QCVN 01 / Thông tư 01 (mật độ), Nghị định 10 / Thông tư 11 (chi phí, hợp đồng).
- **Kiểm tra tuân thủ PCCC**: Nhập thông số hồ sơ (số tầng, chiều cao, diện tích sàn, lối thoát nạn, sprinkler...) → hệ thống đối chiếu với quy chuẩn và báo đạt/không đạt.
- **Kiểm tra mật độ xây dựng**: Nhập diện tích lô, diện tích xây dựng, tổng diện tích sàn → kiểm tra mật độ thuần và FAR theo quy định tham khảo.

## Yêu cầu

- Python 3.10+
- RAM khuyến nghị ≥ 4GB (model embedding ~500MB)

## Cài đặt

```bash
cd legal-bidding-ai
python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
```

(Tùy chọn) Tạo file `.env` và thêm `OPENAI_API_KEY=sk-...` nếu muốn dùng GPT để trả lời chat chi tiết hơn. Không có key vẫn chạy được — hệ thống trả lời dựa trên ngữ cảnh thuần.

## Chạy ứng dụng

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Mở trình duyệt: **http://localhost:8000**

## Deploy lên Vercel

Giao diện có thể deploy lên [Vercel](https://vercel.com/amax888s-projects); backend FastAPI cần host riêng (Railway, Render...). Xem chi tiết từng bước trong **[DEPLOY_VERCEL.md](DEPLOY_VERCEL.md)**.

- Tab **Tra cứu Chat**: Gõ câu hỏi (VD: "lối thoát nạn tối thiểu bao nhiêu mét?", "mật độ xây dựng lô 300m2").
- Tab **Kiểm tra PCCC**: Điền thông số thiết kế → bấm kiểm tra.
- Tab **Mật độ xây dựng**: Điền diện tích lô, diện tích xây dựng, tổng sàn → bấm kiểm tra.

## Khắc phục lỗi "Building wheel for chroma-hnswlib" (Windows)

Lỗi **Microsoft Visual C++ 14.0 or greater is required** khi cài ChromaDB do package `chroma-hnswlib` cần biên dịch C++.

**Cách 1 (khuyến nghị):** Dự án mặc định dùng **FAISS** thay ChromaDB — không cần cài Visual C++ Build Tools. Trong `requirements.txt` đã dùng `faiss-cpu` (có sẵn wheel). Chỉ cần:

```bash
pip install -r requirements.txt
```

**Cách 2:** Nếu muốn dùng ChromaDB, cài [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/), chọn workload "Desktop development with C++", sau đó `pip install chromadb`. Trong `.env` đặt `USE_FAISS=0`.

## Cấu trúc thư mục

```
legal-bidding-ai/
├── main.py              # FastAPI: /api/chat, /api/compliance/pccc, /api/compliance/density, /api/ingest
├── config.py            # Cấu hình đường dẫn, RAG, API key
├── requirements.txt
├── data/
│   ├── documents/       # Thêm file .txt, .md, .pdf, .docx tại đây để mở rộng cơ sở văn bản
│   └── chroma_db/       # Vector store FAISS/Chroma (tự tạo khi chạy)
├── rag/
│   ├── loader.py        # Đọc PDF, DOCX, TXT, MD
│   ├── splitter.py      # Chia văn bản thành chunk
│   ├── embedding.py     # Embedding đa ngôn ngữ (tiếng Việt)
│   ├── store.py         # Vector store (FAISS mặc định hoặc ChromaDB)
│   ├── store_faiss.py   # Backend FAISS (không cần build C++)
│   └── answer.py        # Tổng hợp câu trả lời (ngữ cảnh thuần hoặc OpenAI)
├── compliance/
│   └── checker.py      # Logic kiểm tra PCCC và mật độ
└── static/
    └── index.html      # Giao diện chat + form kiểm tra
```

## Mở rộng dữ liệu

- Bỏ thêm file **.txt**, **.md**, **.pdf**, **.docx** vào `data/documents/` (có thể tạo thư mục con).
- Gọi **POST /api/ingest** để xây lại vector store (hoặc khởi động lại app — lần đầu chạy sẽ tự build từ `data/documents/`).

## API nhanh

- `POST /api/chat` — body: `{"message": "câu hỏi"}` → trả lời RAG.
- `POST /api/compliance/pccc` — body: `so_tang`, `chieu_cao_m`, `dien_tich_san_moi_tang_m2`, `so_loi_thoat`, `chieu_rong_loi_thoat_m`, `khoang_cach_xa_nhat_den_cua_thoat_m`, `co_sprinkler`, `loai_nha`.
- `POST /api/compliance/density` — body: `dien_tich_lot_m2`, `dien_tich_xay_dung_m2`, `tong_dien_tich_san_m2`, `so_tang`.

## Lưu ý pháp lý

Các văn bản trong `data/documents/` là **trích yếu tham khảo**. Khi áp dụng thực tế cần đối chiếu với văn bản gốc và quy định địa phương.
