"""
Task 4 — Chunking, embedding và indexing.

Luồng: đọc Markdown trong data/standardized/ -> chunk -> embed bằng một provider
duy nhất (theo EMBEDDING_PROVIDER trong .env) -> upsert vào ChromaDB (cosine).

Mỗi document/chunk theo docs/MODULE_CONTRACTS.md. ID ổn định để chạy lại không
tạo dữ liệu trùng. Task 5 dùng chung embed_texts() và get_collection().
"""

import csv
import functools
import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

# Giải thích lựa chọn tham số trong báo cáo nhóm.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536

COLLECTION_NAME = "rag_documents"


# --------------------------------------------------------------------------- #
# Embedding (một provider duy nhất, chọn qua .env)
# --------------------------------------------------------------------------- #
@functools.lru_cache(maxsize=2)
def _load_sentence_transformer(model_name: str):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Sinh embedding cho danh sách text, dispatch theo EMBEDDING_PROVIDER."""
    provider = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers").strip()
    model_name = os.getenv("EMBEDDING_MODEL", EMBEDDING_MODEL).strip()
    texts = list(texts)

    if provider == "sentence_transformers":
        model = _load_sentence_transformer(model_name)
        # normalize để dùng cosine distance trong Chroma
        vectors = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
        return vectors.tolist()

    if provider == "openai":
        from openai import OpenAI

        client = OpenAI()
        response = client.embeddings.create(model=model_name, input=texts)
        return [item.embedding for item in response.data]

    if provider == "gemini":
        from google import genai

        client = genai.Client()
        result = client.models.embed_content(model=model_name, contents=texts)
        return [list(embedding.values) for embedding in result.embeddings]

    raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {provider!r}")


def get_collection():
    """Mở/ tạo Chroma collection dùng cosine distance (persistent)."""
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


# --------------------------------------------------------------------------- #
# Load documents
# --------------------------------------------------------------------------- #
@functools.lru_cache(maxsize=1)
def _legal_metadata() -> dict[str, dict[str, str]]:
    """Đọc sources.csv (Task 1) để lấy title/url thật cho tài liệu legal."""
    csv_path = STANDARDIZED_DIR.parent / "landing" / "legal" / "sources.csv"
    mapping: dict[str, dict[str, str]] = {}
    if csv_path.exists():
        with csv_path.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                stem = Path(row["filename"]).stem
                mapping[stem] = {"title": row["title"], "url": row["source_url"]}
    return mapping


def _extract_title_and_url(text: str) -> tuple[str | None, str | None]:
    """Lấy title (dòng '# ...') và url (dòng '**Source:** ...') từ header news."""
    title = url = None
    for line in text.splitlines()[:10]:
        stripped = line.strip()
        if title is None and stripped.startswith("# "):
            title = stripped[2:].strip()
        if stripped.startswith("**Source:**"):
            url = stripped.split("**Source:**", 1)[1].strip() or None
    return title, url


def load_documents() -> list[dict]:
    """Đọc mọi .md trong data/standardized/ và trả về danh sách Document."""
    legal_meta = _legal_metadata()
    documents: list[dict] = []

    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        content = path.read_text(encoding="utf-8")
        doc_type = "legal" if "legal" in path.parts else "news"
        header_title, header_url = _extract_title_and_url(content)

        if doc_type == "legal" and path.stem in legal_meta:
            title = legal_meta[path.stem]["title"]
            url = legal_meta[path.stem]["url"]
        else:
            title = header_title or path.stem
            url = header_url

        documents.append(
            {
                "id": path.relative_to(STANDARDIZED_DIR).as_posix(),
                "content": content,
                "metadata": {
                    "source": path.name,
                    "title": title,
                    "doc_type": doc_type,
                    "url": url,
                },
            }
        )
    return documents


# --------------------------------------------------------------------------- #
# Chunk
# --------------------------------------------------------------------------- #
def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chia Document thành chunks có id ổn định và chunk_index."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks: list[dict] = []
    for document in documents:
        pieces = splitter.split_text(document["content"])
        for index, text in enumerate(pieces):
            if not text.strip():
                continue
            chunks.append(
                {
                    "id": f"{document['id']}::chunk-{index}",
                    "content": text,
                    "metadata": {**document["metadata"], "chunk_index": index},
                }
            )
    return chunks


# --------------------------------------------------------------------------- #
# Embed + index
# --------------------------------------------------------------------------- #
def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Thêm embedding vào từng chunk (giữ nguyên các field khác)."""
    vectors = embed_texts([chunk["content"] for chunk in chunks])
    for chunk, vector in zip(chunks, vectors):
        chunk["embedding"] = vector
    return chunks


def _clean_metadata(metadata: dict) -> dict:
    """Chroma không nhận giá trị None -> loại bỏ key có value None."""
    return {key: value for key, value in metadata.items() if value is not None}


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Upsert chunks vào ChromaDB (id ổn định nên chạy lại không nhân đôi)."""
    collection = get_collection()
    collection.upsert(
        ids=[chunk["id"] for chunk in chunks],
        documents=[chunk["content"] for chunk in chunks],
        embeddings=[chunk["embedding"] for chunk in chunks],
        metadatas=[_clean_metadata(chunk["metadata"]) for chunk in chunks],
    )


def run_pipeline() -> None:
    """Chạy load, chunk, embed và index."""
    documents = load_documents()
    print(f"Loaded {len(documents)} documents")
    chunks = chunk_documents(documents)
    print(f"Created {len(chunks)} chunks")
    embedded_chunks = embed_chunks(chunks)
    index_to_vectorstore(embedded_chunks)
    print(f"Indexed {len(embedded_chunks)} chunks into '{COLLECTION_NAME}'")


if __name__ == "__main__":
    run_pipeline()
