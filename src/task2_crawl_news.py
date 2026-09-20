"""
Task 2 — Crawl bài viết/thông báo.

Chủ đề: học phí – học bổng – hỗ trợ tài chính (nguồn ts.hust.edu.vn).

Năm bài viết này đã được thu thập trước đó (bản Markdown kèm frontmatter có
``source_url``) và được copy vào repo tại data/raw/news_day7/ để repo tự chứa.
``crawl_article`` ưu tiên đọc bản Markdown cục bộ này; nếu không tìm thấy
(URL mới), nó crawl trực tiếp bằng Crawl4AI.

Mỗi bài lưu thành một JSON trong data/landing/news/ với đủ:
    url, title, date_crawled, content_markdown

Cài browser trước khi crawl online:
    python -m playwright install chromium
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

# Bản Markdown nguồn đã được copy vào repo (self-contained, không tham chiếu offline).
LOCAL_CORPUS = Path(__file__).parent.parent / "data" / "raw" / "news_day7"

ARTICLE_URLS = [
    "https://ts.hust.edu.vn/tin-tuc/ho-tro-tai-chinh-cho-sinh-vien",
    "https://ts.hust.edu.vn/tin-tuc/hoc-phi-dai-hoc-2022",
    "https://ts.hust.edu.vn/tin-tuc/mo-dang-ky-hoc-bong-ho-tro-hoc-tap-cho-hoc-sinh-nam-cuoi-thpt",
    "https://ts.hust.edu.vn/tin-tuc/chi-tiet-55-chuong-trinh-dao-tao-tai-bach-khoa-ha-noi-nhan-hoc-bong-chinh-phu-theo-nghi-dinh-179",
    "https://ts.hust.edu.vn/tin-tuc/tieu-chi-xet-hoc-bong-ho-tro-hoc-tap",
]


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Tách frontmatter YAML đơn giản (key: value) và phần thân Markdown."""
    if not text.startswith("---"):
        return {}, text
    _, _, rest = text.partition("---\n")
    front, sep, body = rest.partition("\n---")
    if not sep:
        return {}, text
    meta: dict[str, str] = {}
    for line in front.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, body.lstrip("\n")


def _from_local_corpus(url: str) -> dict | None:
    """Tìm bản đã thu thập ở Day 7 có source_url trùng khớp."""
    if not LOCAL_CORPUS.is_dir():
        return None
    for path in sorted(LOCAL_CORPUS.glob("*.md")):
        meta, body = _parse_frontmatter(path.read_text(encoding="utf-8"))
        if meta.get("source_url") == url:
            return {
                "url": url,
                "title": meta.get("title", path.stem),
                "date_crawled": datetime.now().isoformat(),
                "content_markdown": body.strip(),
            }
    return None


async def _crawl_online(url: str) -> dict:
    """Crawl trực tiếp bằng Crawl4AI (cho URL chưa có sẵn cục bộ)."""
    from crawl4ai import AsyncWebCrawler

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        return {
            "url": url,
            "title": (result.metadata or {}).get("title", "Unknown"),
            "date_crawled": datetime.now().isoformat(),
            "content_markdown": result.markdown or "",
        }


async def crawl_article(url: str) -> dict:
    """Lấy nội dung một bài: ưu tiên bản Day 7, nếu không có thì crawl online."""
    local = _from_local_corpus(url)
    if local and local["content_markdown"]:
        print(f"Reused Day7: {url}")
        return local
    return await _crawl_online(url)


async def crawl_all() -> None:
    """Thu thập và lưu từng bài thành một file JSON."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for index, url in enumerate(ARTICLE_URLS, 1):
        try:
            article = await crawl_article(url)
            output = DATA_DIR / f"article_{index:02d}.json"
            output.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"Saved: {output}")
        except Exception as error:
            print(f"Failed: {url} — {error}")


if __name__ == "__main__":
    asyncio.run(crawl_all())
