| STT | Họ và tên đầy đủ | MSSV | GitHub username | Vai trò | Công việc |
|---:|---|---|---|---|---|
| 1 | Nguyễn Sơn Giang | 2A202602747 | songiangvn | Data Ingestion | Thu thập 3 nghị định (81/2021, 238/2025, 179/2026) + OCR tiếng Việt (tesseract/ocrmypdf), crawl 5 bài news, ghi metadata `sources.csv` — Bước 1–2 (`task1`, `task2`) |
| 3 | Nguyễn Ngọc Thái An | 2A202602462 | nnthaian | Chuẩn hóa & Index | Convert PDF/JSON → Markdown, chunking (500/50), embedding OpenAI, index ChromaDB — Bước 3–5 (`task3`, `task4`) |
| 4 | Lê Tuấn Anh | 2A202602952 | anhltsefpt | Generation, UI & Evaluation | Generation có citation, Streamlit UI, golden dataset 15 case, đánh giá A/B + `RESULT.md` — Bước 8–9 (`task10`, `app.py`, `scripts/evaluate_rag.py`) |
| 5 | Vũ Thường Tín | 2A202602955 | Nituv05 | Retrieval Engine | Semantic search (dense), BM25 lexical, RRF fusion, pipeline + fallback — Bước 6–7 (`task5`, `task6`, `task7`, `task9`) |

## Việc chung (cả nhóm)

- **Bước 10 — nộp bài:** mỗi thành viên tự viết `INDIVIDUAL_REPORT.md`; kiểm repo không lộ `.env`/API key; cùng review báo cáo evaluation.
- **PageIndex (`task8`):** cả nhóm thống nhất **không sử dụng** — fallback được xử lý an toàn ở pipeline (`task9`).
