"""
Task 3 — Chuẩn hóa dữ liệu sang Markdown.

    1. Legal: dùng MarkItDown convert PDF (đã OCR ở Task 1) -> standardized/legal/.
    2. News: đọc JSON, gắn header metadata ở đầu file -> standardized/news/.
    3. Giữ nguyên cấu trúc legal/ và news/, ghi đè khi chạy lại (không tạo bản sao).
"""

import json
from pathlib import Path


LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


def convert_legal_docs() -> None:
    """Convert PDF/DOCX trong landing/legal -> standardized/legal (Markdown)."""
    from markitdown import MarkItDown

    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    converter = MarkItDown()
    for path in sorted(legal_dir.iterdir()):
        if path.suffix.lower() not in {".pdf", ".doc", ".docx"}:
            continue
        result = converter.convert(str(path))
        content = (result.text_content or "").strip()
        if not content:
            print(f"Skip (empty text): {path.name} — kiểm tra lại bước OCR ở Task 1")
            continue
        header = f"# {path.stem}\n\n**Source file:** {path.name}\n\n---\n\n"
        (output_dir / f"{path.stem}.md").write_text(header + content, encoding="utf-8")
        print(f"Legal: {path.name} -> {path.stem}.md ({len(content)} chars)")


def convert_news_articles() -> None:
    """Convert JSON trong landing/news -> standardized/news (Markdown + metadata)."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    for path in sorted(news_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        header = (
            f"# {data['title']}\n\n"
            f"**Source:** {data['url']}\n\n"
            f"**Crawled:** {data['date_crawled']}\n\n---\n\n"
        )
        body = data.get("content_markdown", "").strip()
        (output_dir / f"{path.stem}.md").write_text(header + body, encoding="utf-8")
        print(f"News: {path.name} -> {path.stem}.md")


def convert_all() -> None:
    """Convert toàn bộ dữ liệu landing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    convert_legal_docs()
    convert_news_articles()
    print(f"Saved Markdown to: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()
