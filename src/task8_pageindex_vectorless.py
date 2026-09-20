"""
Task 8 — PageIndex vectorless fallback.

Hướng dẫn:
    1. Đọc PAGEINDEX_API_KEY từ .env.
    2. Upload tài liệu ở định dạng PageIndex hỗ trợ.
    3. Cache document IDs để không upload lại.
    4. Parse kết quả thành SearchResult có method pageindex.

PageIndex là dịch vụ ngoài: cần timeout và xử lý lỗi để pipeline không crash.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any

from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CACHE_FILE = Path(__file__).parent.parent / "pageindex_cache.json"

# Import chunking functions from Task 4 to reuse the same chunking strategy
from src.task4_chunking_indexing import load_documents, chunk_documents


def _load_cache() -> Dict[str, Any]:
    """Load the cache from disk if it exists."""
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _save_cache(cache: Dict[str, Any]) -> None:
    """Save the cache to disk."""
    try:
        CACHE_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
    except IOError as e:
        print(f"Warning: Could not save PageIndex cache: {e}")


def upload_documents() -> None:
    """Upload tài liệu và lưu document IDs để tái sử dụng."""
    if not PAGEINDEX_API_KEY:
        print("Warning: PAGEINDEX_API_KEY not set, skipping upload")
        return

    try:
        from pageindex import PageIndex
    except ImportError:
        print("Error: pageindex package not installed. Install with: pip install pageindex")
        return

    # Initialize PageIndex client
    try:
        client = PageIndex(api_key=PAGEINDEX_API_KEY)
    except Exception as e:
        print(f"Error initializing PageIndex client: {e}")
        return

    # Load existing cache
    cache = _load_cache()
    print(f"Loaded {len(cache)} cached document chunks from PageIndex")

    # Load and chunk documents using the same strategy as Task 4
    try:
        documents = load_documents()
        chunks = chunk_documents(documents)
        print(f"Loaded {len(documents)} documents, split into {len(chunks)} chunks")
    except Exception as e:
        print(f"Error loading documents: {e}")
        return

    # Upload each chunk that hasn't been uploaded yet
    uploaded_count = 0
    for chunk in chunks:
        chunk_id = chunk["id"]
        if chunk_id in cache:
            continue  # Already uploaded

        try:
            # Upload the chunk content to PageIndex
            # We use the chunk's content as the document to index
            # and set the external_id to our chunk ID so we can retrieve it later
            response = client.upload_document(
                content=chunk["content"],
                external_id=chunk_id,
                # Optional: add metadata if the SDK supports it
                metadata=chunk["metadata"]
            )
            
            # Store the chunk data in our cache for later retrieval
            # We store the content and metadata so we can return them in search results
            cache[chunk_id] = {
                "content": chunk["content"],
                "metadata": chunk["metadata"]
            }
            uploaded_count += 1
            print(f"Uploaded chunk {chunk_id} to PageIndex")
            
        except Exception as e:
            print(f"Error uploading chunk {chunk_id}: {e}")
            # Continue with other chunks

    # Save updated cache
    if uploaded_count > 0:
        _save_cache(cache)
        print(f"Uploaded {uploaded_count} new chunks to PageIndex. Total cached: {len(cache)}")
    else:
        print("No new chunks to upload")


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Trả về pageindex SearchResult."""
    if not PAGEINDEX_API_KEY:
        print("Warning: PAGEINDEX_API_KEY not set, returning empty results")
        return []

    try:
        from pageindex import PageIndex
    except ImportError:
        print("Error: pageindex package not installed. Install with: pip install pageindex")
        return []

    # Initialize PageIndex client
    try:
        client = PageIndex(api_key=PAGEINDEX_API_KEY)
    except Exception as e:
        print(f"Error initializing PageIndex client: {e}")
        return []

    # Load cache
    cache = _load_cache()
    if not cache:
        print("Warning: PageIndex cache is empty. Consider running upload_documents() first.")
        return []

    try:
        # Search PageIndex
        # We assume the search method returns a list of results with external_id and score
        results = client.search(
            query=query,
            top_k=top_k
        )
        
        # Convert to our SearchResult format
        search_results: List[Dict[str, Any]] = []
        for res in results:
            external_id = res.get("external_id")
            score = res.get("score", 0.0)
            
            if external_id is None or external_id not in cache:
                continue
                
            chunk_data = cache[external_id]
            search_results.append({
                "id": external_id,
                "content": chunk_data["content"],
                "score": float(score),
                "metadata": chunk_data["metadata"],
                "retrieval_method": "pageindex"
            })
        
        # Sort by score descending (just in case)
        search_results.sort(key=lambda x: x["score"], reverse=True)
        return search_results[:top_k]
        
    except Exception as e:
        print(f"Error during PageIndex search: {e}")
        return []


if __name__ == "__main__":
    upload_documents()