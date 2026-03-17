# Deploy lên Vercel

[Vercel](https://vercel.com) phù hợp để host **giao diện (frontend)** của Legal & Bidding AI. **Backend FastAPI** (RAG, model, FAISS) cần host ở dịch vụ khác (Railway, Render, Fly.io...) vì Vercel serverless có giới hạn dung lượng và thời gian chạy.

## Kiến trúc deploy

- **Vercel**: Giao diện web (HTML/JS) + API `/api/config` (trả về URL backend).
- **Backend**: Chạy FastAPI ở Railway / Render / Fly.io / VPS, sau đó khai báo URL này vào Vercel.

---

## Bước 1: Deploy Backend (chọn 1 trong các cách)

Backend phải chạy ở nơi có Python, đủ RAM và có thể public URL.

### Cách A: Railway (khuyến nghị, có free tier)

1. Vào [railway.app](https://railway.app), đăng nhập (GitHub).
2. **New Project** → **Deploy from GitHub repo**. Chọn repo chứa project `legal-bidding-ai`.
3. Trong project, chọn service → **Settings**:
   - **Root Directory**: `legal-bidding-ai` (nếu repo có nhiều folder).
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. **Variables**: thêm `PORT` (Railway thường tự gán). Nếu dùng OpenAI: thêm `OPENAI_API_KEY`.
5. **Deploy** → sau khi chạy xong, vào **Settings** → **Networking** → **Generate Domain** → copy URL (vd: `https://xxx.up.railway.app`).

### Cách B: Render

1. Vào [render.com](https://render.com) → **New** → **Web Service**.
2. Kết nối repo, chọn repo và branch.
3. **Root Directory**: `legal-bidding-ai`.
4. **Build Command**: `pip install -r requirements.txt`
5. **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. **Instance**: chọn plan (free tier có thể bị sleep sau 15 phút không dùng).
7. Deploy xong, copy URL dịch vụ (vd: `https://legal-ai-xxx.onrender.com`).

### Cách C: Chạy backend trên máy / VPS

Nếu bạn chạy backend trên máy hoặc VPS có IP public:

```bash
cd legal-bidding-ai
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Cần mở port 8000 (firewall) và nếu dùng HTTPS hoặc tên miền thì cấu hình thêm. URL backend sẽ là `http://IP:8000` hoặc `https://your-domain.com`.

---

## Bước 2: Deploy Frontend lên Vercel

### 2.1. Đẩy code lên GitHub

Nếu chưa có repo:

```bash
cd c:\Users\Admin\Downloads\Trade\legal-bidding-ai
git init
git add .
git commit -m "Legal Bidding AI - ready for Vercel"
```

Tạo repo mới trên GitHub (vd: `amax888s/legal-bidding-ai`), rồi:

```bash
git remote add origin https://github.com/amax888s/legal-bidding-ai.git
git branch -M main
git push -u origin main
```

### 2.2. Kết nối Vercel với GitHub

1. Đăng nhập [Vercel](https://vercel.com) (GitHub / Google / Email).
2. Vào **Add New…** → **Project** (hoặc dashboard [amax888s-projects](https://vercel.com/amax888s-projects)).
3. **Import** repo GitHub vừa push (vd: `legal-bidding-ai`).
4. Cấu hình project:
   - **Framework Preset**: Other
   - **Root Directory**: để mặc định (root repo) hoặc chọn folder chứa `vercel.json` và `static/`.
   - **Build Command**: để trống (chỉ cần static + serverless).
   - **Output Directory**: để trống (Vercel dùng `vercel.json` rewrites).

### 2.3. Cấu hình Environment Variable

Trong project Vercel → **Settings** → **Environment Variables**:

| Name               | Value                    | Ghi chú                          |
|--------------------|--------------------------|----------------------------------|
| `LEGAL_AI_API_URL` | `https://xxx.up.railway.app` | URL backend (Railway/Render/…) **không** dấu `/` cuối |

Ví dụ:

- Railway: `https://legal-ai-production.up.railway.app`
- Render: `https://legal-ai-xxx.onrender.com`

Lưu (Save), sau đó **Redeploy** project (Deployments → ... → Redeploy) để biến môi trường có hiệu lực.

### 2.4. Deploy

Bấm **Deploy**. Khi build xong, Vercel sẽ cho URL dạng:

- `https://legal-bidding-ai-xxx.vercel.app`
- hoặc custom domain nếu bạn đã thêm.

Mở URL này trên trình duyệt: giao diện sẽ gọi API qua `LEGAL_AI_API_URL` (backend bạn đã deploy ở bước 1).

---

## Kiểm tra sau khi deploy

1. Mở trang Vercel (vd: `https://legal-bidding-ai-xxx.vercel.app`).
2. Mở DevTools (F12) → tab **Network**.
3. Gửi một câu hỏi ở tab **Tra cứu Chat**.
4. Request phải gửi đến **URL backend** (đã cấu hình trong `LEGAL_AI_API_URL`), không phải domain Vercel. Nếu 404 hoặc CORS lỗi thì kiểm tra:
   - Backend đã chạy và URL đúng.
   - Biến `LEGAL_AI_API_URL` trên Vercel đúng, không thừa dấu `/` cuối.
   - Backend đã bật CORS (trong `main.py` đã có `allow_origins=["*"]`).

---

## Chạy full stack local (không dùng Vercel)

```bash
cd legal-bidding-ai
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Mở http://localhost:8000 — frontend và backend cùng gốc, không cần `LEGAL_AI_API_URL`.
