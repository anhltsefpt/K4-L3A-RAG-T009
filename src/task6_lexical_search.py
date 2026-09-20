"""
Task 6 — Lexical search bằng BM25.

Dùng cùng corpus chunks với Task 5 (đọc lại từ collection ChromaDB đã index ở
Task 4). BM25 phù hợp với từ khóa chính xác, mã tài liệu và tên riêng. Output
theo SearchResult và sort score giảm dần.
"""

import re


CORPUS: list[dict] = []
_BM25 = None


def _tokenize(text: str) -> list[str]:
    """Tách token unicode (giữ chữ tiếng Việt có dấu), hạ thường."""
    return re.findall(r"\w+", text.lower())


def _load_corpus() -> list[dict]:
    """Đọc lại toàn bộ chunk đã index để dùng chung corpus với Task 5."""
    from .task4_chunking_indexing import get_collection

    data = get_collection().get(include=["documents", "metadatas"])
    corpus = []
    for item_id, content, metadata in zip(
        data["ids"], data["documents"], data["metadatas"]
    ):
        metadata = dict(metadata)
        metadata.setdefault("url", None)  # contract yêu cầu key 'url' luôn tồn tại
        corpus.append({"id": item_id, "content": content, "metadata": metadata})
    return corpus


def build_bm25_index(corpus: list[dict]):
    """Tạo BM25 index từ cùng corpus chunks của Task 4."""
    from rank_bm25 import BM25Okapi

    tokenized = [_tokenize(item["content"]) for item in corpus]
    return BM25Okapi(tokenized)


def _ensure_index():
    """Lazy-load corpus và BM25 index (cache lại giữa các lần gọi)."""
    global _BM25
    if not CORPUS:
        CORPUS.extend(_load_corpus())
    if _BM25 is None:
        _BM25 = build_bm25_index(CORPUS)
    return _BM25


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    if top_k <= 0 or not query.strip():
        return []

    query_tokens = set(_tokenize(query))
    bm25 = _ensure_index()
    scores = bm25.get_scores(_tokenize(query))
    # sort ổn định (giữ thứ tự corpus khi score bằng nhau)
    indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

    results = []
    for index in indices:
        score = float(scores[index])
        item = CORPUS[index]
        # Bỏ chunk vô nghĩa: score <= 0 VÀ không chia sẻ token nào với query.
        # (Corpus rất nhỏ có thể cho BM25=0 dù chunk thực sự chứa từ khóa -> vẫn giữ.)
        if score <= 0 and query_tokens.isdisjoint(_tokenize(item["content"])):
            continue
        results.append(
            {
                "id": item["id"],
                "content": item["content"],
                "score": score,
                "metadata": item["metadata"],
                "retrieval_method": "bm25",
            }
        )
    return results


if __name__ == "__main__":
    for result in lexical_search("mức trần học phí", top_k=3):
        print(result["score"], result["metadata"]["title"][:50])
