# Tổng hợp câu trả lời từ ngữ cảnh RAG (có thể kết hợp LLM)
from typing import List, Optional

def build_context_from_docs(docs: List[dict]) -> str:
    """Gộp các đoạn retrieval thành một khối ngữ cảnh có đánh số nguồn."""
    parts = []
    for i, d in enumerate(docs, 1):
        src = d.get("source", "Nguồn")
        content = d.get("content", "")
        parts.append(f"[{i}] ({src})\n{content}")
    return "\n\n---\n\n".join(parts)

def answer_from_context_only(query: str, docs: List[dict]) -> str:
    """Trả lời dựa trên ngữ cảnh thuần (không cần LLM): tóm tắt và trích dẫn."""
    if not docs:
        return (
            "Không tìm thấy đoạn văn bản phù hợp trong cơ sở dữ liệu. "
            "Bạn có thể thử từ khóa khác hoặc bổ sung thêm văn bản vào thư mục data/documents."
        )
    context = build_context_from_docs(docs)
    return (
        f"Dựa trên các văn bản liên quan, thông tin tham khảo như sau:\n\n{context}\n\n"
        "※ Lưu ý: Đây là thông tin tra cứu tự động, cần đối chiếu với văn bản gốc khi áp dụng."
    )

def answer_with_llm(query: str, docs: List[dict], api_key: str) -> str:
    """Dùng OpenAI (hoặc tương thích) để sinh câu trả lời từ query + context."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        context = build_context_from_docs(docs)
        if not context.strip():
            return answer_from_context_only(query, docs)
        system = (
            "Bạn là trợ lý pháp lý chuyên về xây dựng tại Việt Nam. "
            "Trả lời dựa CHỦ YẾU vào các đoạn văn bản được cung cấp trong ngữ cảnh. "
            "Nếu không đủ thông tin, nói rõ và gợi ý tra cứu thêm. Trả lời bằng tiếng Việt."
        )
        user_content = f"Câu hỏi: {query}\n\nNgữ cảnh từ văn bản:\n{context}"
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            max_tokens=1500,
        )
        return resp.choices[0].message.content or answer_from_context_only(query, docs)
    except Exception as e:
        return (
            f"Không thể gọi LLM ({e}). Đang trả lời theo ngữ cảnh thuần.\n\n"
            + answer_from_context_only(query, docs)
        )

def generate_answer(
    query: str,
    docs: List[dict],
    openai_api_key: Optional[str] = None,
) -> str:
    """Chọn cách trả lời: có API key thì dùng LLM, không thì dùng ngữ cảnh thuần."""
    if openai_api_key and openai_api_key.strip():
        return answer_with_llm(query, docs, openai_api_key.strip())
    return answer_from_context_only(query, docs)
