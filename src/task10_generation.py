"""
Task 10 — Generation có citation.

Hướng dẫn:
    1. Retrieve top-k chunks.
    2. Reorder để giảm lost-in-the-middle.
    3. Format context kèm title và source.
    4. Gọi provider được chọn trong .env.
    5. Trả answer, sources và retrieval_source.

Nếu context không đủ hoặc provider lỗi, trả safe refusal; không bịa thông tin.
"""

import os

from dotenv import load_dotenv

from .task9_retrieval_pipeline import retrieve


load_dotenv()

TOP_K = 5
TOP_P = 0.9
TEMPERATURE = 0.3

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "")

SYSTEM_PROMPT = """Trả lời chỉ từ context được cung cấp.
Mỗi khẳng định phải có citation. Nếu thiếu evidence, hãy từ chối xác minh."""


SAFE_REFUSAL = "Tôi không thể xác minh thông tin này từ nguồn hiện có."


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """Đưa chunks quan trọng về đầu và cuối context (giảm lost-in-the-middle).

    Không mutate input, không đổi/mất ID — chỉ đổi vị trí.
    """
    if len(chunks) <= 2:
        return list(chunks)
    front = chunks[::2]        # rank cao nhất (0,2,4...) đưa lên đầu
    back = chunks[1::2]        # rank kế đưa về cuối theo thứ tự đảo
    return front + back[::-1]


def format_context(chunks: list[dict]) -> str:
    """Tạo context có nhãn title + source để câu trả lời trích dẫn kiểm chứng được."""
    parts = []
    for index, chunk in enumerate(chunks, 1):
        metadata = chunk["metadata"]
        parts.append(
            f"[Document {index} | Title: {metadata['title']} | "
            f"Source: {metadata['source']}]\n{chunk['content']}"
        )
    return "\n\n---\n\n".join(parts)


def call_llm(system_prompt: str, user_message: str) -> str:
    """Gọi OpenAI, Gemini hoặc Anthropic theo LLM_PROVIDER; trả text thuần."""
    provider = LLM_PROVIDER.strip().lower()
    model = LLM_MODEL.strip()

    if provider == "openai":
        from openai import OpenAI

        client = OpenAI()
        response = client.chat.completions.create(
            model=model or "gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=TEMPERATURE,
            top_p=TOP_P,
        )
        return (response.choices[0].message.content or "").strip()

    if provider == "gemini":
        from google import genai
        from google.genai import types

        client = genai.Client()
        response = client.models.generate_content(
            model=model or "gemini-1.5-flash",
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=TEMPERATURE,
                top_p=TOP_P,
            ),
        )
        return (response.text or "").strip()

    if provider == "anthropic":
        import anthropic

        client = anthropic.Anthropic()
        response = client.messages.create(
            model=model or "claude-3-5-sonnet-latest",
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            max_tokens=1024,
            temperature=TEMPERATURE,
            top_p=TOP_P,
        )
        return "".join(block.text for block in response.content if block.type == "text").strip()

    raise ValueError(f"Unsupported LLM_PROVIDER: {provider!r}")


def _refusal(sources: list[dict], retrieval_source: str) -> dict:
    return {"answer": SAFE_REFUSAL, "sources": sources, "retrieval_source": retrieval_source}


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """Trả về GenerationResult (answer, sources, retrieval_source đồng bộ)."""
    chunks = retrieve(query, top_k=top_k)
    if not chunks:
        # thiếu evidence -> safe refusal
        return _refusal([], "none")

    # retrieval_source mô tả đường tạo ra sources (hybrid | pageindex)
    method = chunks[0]["retrieval_method"]
    retrieval_source = method if method in {"hybrid", "pageindex"} else "hybrid"

    reordered = reorder_for_llm(chunks)
    context = format_context(reordered)
    user_message = f"Context:\n{context}\n\nQuestion: {query}"

    try:
        answer = call_llm(SYSTEM_PROMPT, user_message)
    except Exception:
        # provider lỗi -> không crash UI, trả safe refusal nhưng vẫn kèm nguồn đã truy xuất
        return _refusal(chunks, retrieval_source)

    if not answer:
        return _refusal(chunks, retrieval_source)

    return {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": retrieval_source,
    }


if __name__ == "__main__":
    print(generate_with_citation("test query"))
