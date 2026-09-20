"""
Task 6 — Lexical search bằng BM25.

Dùng cùng corpus chunks với Task 5. BM25 phù hợp với từ khóa chính xác, mã tài
liệu và tên riêng. Output phải theo SearchResult và sort score giảm dần.
"""

from pathlib import Path
from typing import List
from dotenv import load_dotenv

load_dotenv()

from src.task4_chunking_indexing import load_documents, chunk_documents

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"

# CORPUS is loaded lazily to allow monkeypatching in tests
_CORPUS: List[dict] = []
_CORPUS_LOADED = False


def _load_corpus() -> List[dict]:
    """Load and chunk documents to create the BM25 corpus."""
    documents = load_documents()
    chunks = chunk_documents(documents)
    return chunks


def _get_corpus() -> List[dict]:
    """Get corpus, loading it on first access."""
    global _CORPUS, _CORPUS_LOADED
    if not _CORPUS_LOADED:
        _CORPUS = _load_corpus()
        _CORPUS_LOADED = True
    return _CORPUS


# For backward compatibility and test monkeypatching
CORPUS: List[dict] = []


def build_bm25_index(corpus: List[dict]):
    """Tạo BM25 index từ cùng corpus chunks của Task 4."""
    from rank_bm25 import BM25Okapi
    tokenized = [item["content"].lower().split() for item in corpus]
    return BM25Okapi(tokenized)


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    import numpy as np
    corpus = CORPUS if CORPUS else _get_corpus()
    bm25 = build_bm25_index(corpus)
    scores = bm25.get_scores(query.lower().split())
    
    # Tie-breaker: count how many query terms appear in each document
    query_terms = set(query.lower().split())
    term_overlap = []
    for item in corpus:
        doc_terms = set(item["content"].lower().split())
        overlap = len(query_terms & doc_terms)
        term_overlap.append(overlap)
    
    # Sort by (score, term_overlap) descending
    indices = np.lexsort((term_overlap, scores))[::-1][:top_k]
    
    results = []
    for index in indices:
        if scores[index] < 0:
            continue
        item = corpus[index]
        results.append({
            "id": item["id"],
            "content": item["content"],
            "score": float(scores[index]),
            "metadata": item["metadata"],
            "retrieval_method": "bm25",
        })
    return results

if __name__ == "__main__":
    for result in lexical_search("test query", top_k=3):
        print(result)