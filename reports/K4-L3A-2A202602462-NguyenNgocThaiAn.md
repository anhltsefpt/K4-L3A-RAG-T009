# Individual contribution report

---

## Thông tin

- Họ và tên: Nguyễn Ngọc Thái An
- Mã học viên: 2A202602462
- Nhóm: T-009
- Repository/branch: nnthaian

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 3 — Chuẩn hóa dữ liệu sang Markdown | Thiết kế và chuẩn hóa quy trình chuyển dữ liệu vào dạng Markdown để đồng bộ định dạng giữa legal/news; đảm bảo metadata theo contract và giữ cấu trúc thư mục `data/standardized/*`. | `src/task3_convert_markdown.py` | Done |
| Task 4 — Chunking, embedding và indexing | Xây dựng pipeline chunking `RecursiveCharacterTextSplitter` với `chunk_size=500`, `chunk_overlap=50`, tạo ids ổn định cho mỗi chunk, gọi embedding theo provider cấu hình, và upsert vào ChromaDB với cosine distance. | `src/task4_chunking_indexing.py` | Done |
| Chroma indexing và vector DB bootstrapping | Tạo persistent collection, lưu metadata và chuẩn hóa document/chunk format để Task 5+ có thể đọc trực tiếp bằng shared embedding pipeline. | `src/task4_chunking_indexing.py` | Done |

Chỉ kê khai công việc có thể đối chiếu bằng file, commit, pull request, test hoặc kết quả evaluation.

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Dùng `chunk_size=500` và `chunk_overlap=50` cho mọi chunk.  
   **Lý do/evidence:** Đây là cấu hình được ghi rõ trong `src/task4_chunking_indexing.py` và phù hợp với launch point của pipeline RAG để giữ độ dài chunk vừa đủ cho retrieval và không quá mảnh.  
   **Trade-off:** Tăng độ dài context nhưng giảm số chunk, giúp giảm overhead khi index và search nhưng có thể làm mất một vài chi tiết ngắn ở các tài liệu dài.

2. **Quyết định:** Dùng một shared `embed_texts()` pipeline và Chroma collection có `hnsw:space = cosine` để tất cả retrieval tasks cùng một embedding schema.  
   **Lý do/evidence:** `src/task4_chunking_indexing.py` định nghĩa `embed_texts()` và `get_collection()`, đồng thời `Task 5`/`Task 6`/`Task 7` sử dụng chung corpus/chunk structure.  
   **Trade-off:** Cố định một provider và một schema giúp đơn giản hóa pipeline, nhưng nếu chuyển provider khác thì cần đồng bộ lại model/dimension và cách đánh giá embedding.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng:
  - `python -m src.task4_chunking_indexing`
  - `pytest tests/test_contracts.py -q`
- Kết quả trước/sau nếu có:
  - `pytest tests/test_contracts.py -q` đã chạy thành công trong quá trình hoàn thiện contract check.
  - Pipeline `task4` đã được thực thi để chunk và index dữ liệu vào ChromaDB sau khi hoàn tất.
- Lỗi đã phát hiện và cách xử lý:
  - Vấn đề đầu tiên là `EMBEDDING_PROVIDER` bị rỗng hoặc chưa load từ `.env`, dẫn tới lỗi provider không hợp lệ. Đã fix bằng cách `load_dotenv()` và đảm bảo biến môi trường được đọc từ `.env` trước khi gọi embedding.
  - Vấn đề thứ hai là NVIDIA embedding API chấp nhận tối đa 256 input/request, nên cần batch dữ liệu trong `embed_texts()` để tránh lỗi 400 `input count exceeds maximum allowed batch size`.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm:
  - Pipeline chuẩn hóa và indexing phụ thuộc chặt chẽ vào cấu hình `.env`, đặc biệt với `EMBEDDING_PROVIDER`, `NVIDIA_API_KEY`, `EMBEDDING_MODEL`; nếu chưa cấu hình đúng, pipeline sẽ không index được.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện:
  - Thêm kiểm tra `try/except` rõ ràng và log chi tiết trước khi gọi embedding/index để dễ debug production pipeline, đồng thời chuẩn hóa việc chọn provider theo một registry rõ ràng hơn.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: Nguyễn Ngọc Thái An
