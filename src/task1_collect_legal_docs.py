"""
Task 1 — Thu thập tài liệu chính sách/quy định.

Chủ đề nhóm: Học phí – học bổng – hỗ trợ tài chính cho sinh viên.

Ba nghị định gốc (bản ký số công khai của Chính phủ) được tải thủ công vào
data/landing/legal/. Vì đây là bản scan không có text layer, hàm
``ensure_text_layer`` sẽ dùng ocrmypdf (tesseract tiếng Việt) để nhúng text
layer, giúp Task 3 (MarkItDown) trích được nội dung.

Metadata nguồn được ghi ra data/landing/legal/sources.csv để người khác kiểm
chứng lại.
"""

import csv
import subprocess
from datetime import date
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"

# filename -> metadata nguồn. File PDF đã được tải thủ công từ các URL này.
LEGAL_SOURCES: dict[str, dict[str, str]] = {
    "nghi-dinh-81-2021-nd-cp-hoc-phi.pdf": {
        "title": (
            "Nghị định 81/2021/NĐ-CP quy định về cơ chế thu, quản lý học phí "
            "và chính sách miễn, giảm học phí, hỗ trợ chi phí học tập"
        ),
        "source_url": "https://vanban.chinhphu.vn/default.aspx?pageid=27160&docid=203950",
    },
    "nghi-dinh-179-2026-nd-cp-hoc-bong.pdf": {
        "title": (
            "Nghị định 179/2026/NĐ-CP quy định chính sách học bổng cho người học "
            "các ngành khoa học cơ bản, kỹ thuật then chốt và công nghệ chiến lược"
        ),
        "source_url": "https://chinhphu.vn/?pageid=27160&docid=218222",
    },
    "nghi-dinh-238-2025-nd-cp.pdf": {
        "title": (
            "Nghị định 238/2025/NĐ-CP quy định về chính sách học phí, miễn, giảm, "
            "hỗ trợ học phí, hỗ trợ chi phí học tập và giá dịch vụ trong lĩnh vực "
            "giáo dục, đào tạo"
        ),
        "source_url": "https://vanban.chinhphu.vn/?pageid=27160&docid=215169",
    },
}


def setup_directory() -> None:
    """Tạo thư mục lưu tài liệu gốc."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def has_text_layer(pdf_path: Path) -> bool:
    """True nếu PDF đã có text trích xuất được (không phải scan thuần ảnh)."""
    try:
        from pdfminer.high_level import extract_text
    except ImportError:
        return True  # không có pdfminer thì bỏ qua bước OCR
    text = extract_text(str(pdf_path)) or ""
    # bản scan chỉ trả về ký tự ngắt trang (\x0c); yêu cầu tối thiểu vài trăm ký tự thật
    return len(text.replace("\x0c", "").strip()) >= 200


def ensure_text_layer(pdf_path: Path) -> None:
    """OCR tiếng Việt để nhúng text layer nếu PDF là bản scan."""
    if has_text_layer(pdf_path):
        print(f"Text OK: {pdf_path.name}")
        return
    print(f"OCR (vie): {pdf_path.name} ...")
    subprocess.run(
        [
            "ocrmypdf",
            "-l", "vie",
            "--force-ocr",       # scan không có text -> buộc OCR toàn bộ
            # bản gốc có chữ ký số; corpus chỉ cần text nên chấp nhận vô hiệu chữ ký
            "--invalidate-digital-signatures",
            "--optimize", "1",
            str(pdf_path), str(pdf_path),
        ],
        check=True,
    )


def write_sources_csv() -> None:
    """Ghi metadata nguồn để kiểm chứng."""
    csv_path = DATA_DIR / "sources.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["filename", "title", "source_url", "retrieved_at", "license_or_permission"])
        for filename, meta in LEGAL_SOURCES.items():
            writer.writerow([filename, meta["title"], meta["source_url"], date.today().isoformat(), "public-source"])
    print(f"Metadata: {csv_path}")


def download_documents() -> None:
    """Xác minh tài liệu (tải thủ công), OCR nếu cần và ghi metadata."""
    missing = [name for name in LEGAL_SOURCES if not (DATA_DIR / name).exists()]
    if missing:
        raise FileNotFoundError(
            "Thiếu tài liệu trong data/landing/legal/: "
            + ", ".join(missing)
            + "\nHãy tải thủ công các PDF gốc rồi chạy lại."
        )
    for name in LEGAL_SOURCES:
        ensure_text_layer(DATA_DIR / name)
    write_sources_csv()

    ready = sorted(p.name for p in DATA_DIR.glob("*.pdf"))
    print(f"Collected {len(ready)} legal document(s): {ready}")


if __name__ == "__main__":
    setup_directory()
    download_documents()
