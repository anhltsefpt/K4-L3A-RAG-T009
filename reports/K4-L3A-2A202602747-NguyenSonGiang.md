# Individual contribution report

## Thông tin

- Họ và tên: Nguyễn Sơn Giang
- Mã học viên: 2A202602747
- Nhóm: K4-L3A-RAG-T009
- Repository/branch: github.com/anhltsefpt/K4-L3A-RAG-T009 — `main`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Thu thập 3 tài liệu chính sách | Chọn chủ đề học phí – học bổng – hỗ trợ tài chính; lấy 3 nghị định gốc (81/2021, 238/2025, 179/2026) từ nguồn công khai của Chính phủ; khai báo `LEGAL_SOURCES` (title đầy đủ + `source_url`) | `src/task1_collect_legal_docs.py`, `data/landing/legal/*.pdf` — commit `ad52a79` | Done |
| OCR tiếng Việt cho PDF scan | `has_text_layer` dùng pdfminer để phát hiện bản scan (bỏ ký tự `\x0c`, yêu cầu ≥200 ký tự thật); `ensure_text_layer` gọi `ocrmypdf -l vie --force-ocr --invalidate-digital-signatures --optimize 1` nhúng text layer tại chỗ | `src/task1_collect_legal_docs.py` — commit `ad52a79` | Done |
| Metadata nguồn kiểm chứng được | `write_sources_csv` ghi `filename, title, source_url, retrieved_at, license_or_permission`; `download_documents` fail-fast (`FileNotFoundError` liệt kê đúng file thiếu) thay vì chạy tiếp với corpus khuyết | `data/landing/legal/sources.csv` — commit `ad52a79` | Done |
| Crawl 5 bài news | `_parse_frontmatter` + `_from_local_corpus` khớp bài theo `source_url` từ bản Markdown đã có trong repo; `_crawl_online` (Crawl4AI) cho URL chưa có sẵn; mỗi bài lưu 1 JSON đủ `url/title/date_crawled/content_markdown`; `crawl_all` bắt lỗi từng bài để một URL hỏng không làm chết cả lượt chạy | `src/task2_crawl_news.py`, `data/landing/news/article_01..05.json`, `data/raw/news_day7/` — commit `ad52a79` | Done |

Phạm vi ownership căn cứ `TEAMMATES.md`. Các commit trên `main` được tích hợp/push bằng tài khoản repository chung `anhltsefpt`; bằng chứng đối chiếu là các file dữ liệu, `sources.csv` và acceptance tests nêu dưới đây.

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** OCR ngay ở bước thu thập (Task 1) thay vì để bước convert (Task 3) tự xử lý PDF scan.  
   **Lý do/evidence:** Cả 3 nghị định đều là bản ký số dạng ảnh, không có text layer. MarkItDown trong Task 3 trả về chuỗi rỗng với các file này (`task3_convert_markdown.py` phải in cảnh báo `Skip (empty text) — kiểm tra lại bước OCR ở Task 1`). Sau OCR, corpus chuẩn hóa đạt 31KB / 107KB / 135KB cho ba nghị định, đủ để chunk và index.  
   **Trade-off:** `--force-ocr` ghi đè file gốc và `--invalidate-digital-signatures` vô hiệu chữ ký số — chấp nhận được vì corpus chỉ cần text, nhưng đồng nghĩa PDF trong repo không còn dùng để đối chiếu pháp lý; muốn kiểm chứng phải tải lại từ `source_url`.

2. **Quyết định:** Tài liệu legal tải thủ công + script chỉ *xác minh*, và news ưu tiên đọc bản Markdown đã lưu trong `data/raw/news_day7/` thay vì crawl online mỗi lần chạy.  
   **Lý do/evidence:** Trang `vanban.chinhphu.vn` yêu cầu thao tác trên UI để ra link file, còn `ts.hust.edu.vn` cần Playwright/Chromium. Cách làm hiện tại giúp repo tự chứa và chạy lại cho kết quả giống nhau; `crawl_article` vẫn giữ nhánh `_crawl_online` cho URL mới.  
   **Trade-off:** `date_crawled` trong JSON là thời điểm chạy script chứ không phải thời điểm lấy bài thật (ngày lấy thật được ghi ở `data/raw/news_day7/sources.csv`: 2026-09-19); nếu trang nguồn cập nhật nội dung, repo sẽ không tự phát hiện.

## Kiểm thử và kết quả

- `pytest tests/test_acceptance.py -q`: **5/5 passed** — trong đó `test_corpus_has_required_legal_documents` (≥3 file PDF, mỗi file >1KB) và `test_corpus_has_required_news_with_metadata` (5 JSON, đủ 4 field `url/title/date_crawled/content_markdown` và không field nào rỗng) là hai test trực tiếp phủ phần việc của tôi.
- `pytest -q`: **20/20 passed** (15 contract + 5 acceptance); test suite không gọi mạng thật.
- Kiểm tra thủ công sau OCR: mở `data/standardized/legal/nghi-dinh-179-2026-nd-cp-hoc-bong.md` xác nhận đọc được "Số: 179/2026/NĐ-CP" và các điều khoản; 3 nghị định + 5 bài news cho tổng ~297KB Markdown chuẩn hóa.
- Lỗi đã phát hiện và cách xử lý: (a) chạy lần đầu, MarkItDown trả text rỗng cho cả 3 PDF → bổ sung `has_text_layer`/`ensure_text_layer` trong Task 1; (b) ocrmypdf từ chối xử lý file có chữ ký số → thêm `--invalidate-digital-signatures`; (c) thiếu file PDF trong `data/landing/legal/` từng làm pipeline chạy tiếp với corpus khuyết → đổi sang raise `FileNotFoundError` liệt kê tên file thiếu.

## Điều còn hạn chế

- OCR phần header/con dấu còn nhiễu: trong `nghi-dinh-179-2026-nd-cp-hoc-bong.md`, dòng đầu lẫn ký tự rác của dấu điện tử (`TPP(*)`, `coenGomoi ĐIỆN TỬ CHÍNH PHỦ`) và có lỗi dấu ("học bỗng", "QH1 4"). Đây là một phần nguyên nhân của case #11 trong `group_project/evaluation/RESULT.md` (context_recall = 0 vì số hiệu nghị định nằm ở chunk header nhiễu).
- Nếu có thêm thời gian: làm bước hậu xử lý OCR (cắt bỏ khối header/con dấu, chuẩn hóa dấu tiếng Việt) trước khi giao sang Task 3, và ghi thêm cột `checksum` vào `sources.csv` để phát hiện khi tài liệu nguồn thay đổi.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 2026-09-20
- Tên thành viên: Nguyễn Sơn Giang
