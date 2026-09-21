# Individual contribution report

## Thông tin

- Họ và tên: Vũ Thường Tín
- Mã học viên: 2A202602955
- Nhóm: K4-L3A-RAG-T009
- Repository/branch: github.com/anhltsefpt/K4-L3A-RAG-T009 — `main`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Dense semantic search | Dùng lại `embed_texts()` của Task 4 để bảo đảm cùng embedding model/dimension; truy vấn ChromaDB; đổi cosine distance thành similarity; chuẩn hóa metadata và trả `SearchResult` giảm dần, không vượt `top_k` | `src/task5_semantic_search.py` — commit tích hợp `e76ff7a` | Done |
| BM25 lexical search | Đọc đúng corpus chunk đã index trong ChromaDB; tokenize Unicode giữ tiếng Việt có dấu; lazy-load/cache BM25; xử lý query rỗng, corpus nhỏ và loại kết quả không liên quan | `src/task6_lexical_search.py` — commit tích hợp `e76ff7a` | Done |
| RRF fusion | Cài đặt `sum(1 / (k + rank))` với rank từ 1; hợp nhất theo ID, không cộng trực tiếp cosine với BM25; không mutate đầu vào; gắn `retrieval_method="hybrid"`, sort và cắt `top_k` | `src/task7_reranking.py` — commit tích hợp `d362f2c` | Done |
| Retrieval pipeline và fallback | Chạy dense + BM25 trên cùng corpus, lấy `top_k * 2` ứng viên và fuse RRF đúng một lần; dùng best dense cosine gốc để xét threshold; bắt lỗi PageIndex để pipeline không crash và trả lại hybrid result an toàn | `src/task9_retrieval_pipeline.py` — commit tích hợp `d362f2c` | Done |

Phạm vi ownership căn cứ `TEAMMATES.md`. Các commit trên `main` được tích hợp/push bằng tài khoản repository chung `anhltsefpt`; bằng chứng đối chiếu chính là các module, contract tests và kết quả A/B nêu dưới đây.

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Hợp nhất dense và BM25 bằng thứ hạng RRF, không so sánh hay cộng trực tiếp hai loại score.  
   **Lý do/evidence:** Cosine similarity và BM25 có thang đo khác nhau. RRF theo ID vừa giữ schema chung vừa giúp tài liệu xuất hiện cao ở cả hai danh sách được ưu tiên. Kết quả A/B trên 15 câu cho thấy hybrid + RRF tăng điểm trung bình từ **0.7233 lên 0.8144**, trong đó context recall tăng **0.20**.  
   **Trade-off:** RRF tăng recall nhưng có thể đưa thêm chunk khớp từ khóa mà chưa đủ sát nghĩa; case #5 trong evaluation có context precision giảm từ 1.00 xuống 0.50.

2. **Quyết định:** Fallback chỉ dựa trên best cosine score gốc của dense retrieval và RRF chỉ chạy một lần.  
   **Lý do/evidence:** RRF score phản ánh thứ hạng, không phải độ tương đồng tuyệt đối, nên không phù hợp để so với confidence threshold. Các test kiểm tra riêng việc dùng dense score, số lần fuse và khả năng sống sót khi provider fallback lỗi.  
   **Trade-off:** Nhóm không sử dụng PageIndex, vì vậy khi dense score thấp, pipeline thử fallback nhưng sẽ giữ kết quả hybrid nếu PageIndex không khả dụng; đây là cơ chế an toàn, không phải vectorless fallback đầy đủ.

## Kiểm thử và kết quả

- `pytest tests/test_contracts.py -q`: **15/15 passed**; bao phủ signature, schema/order/unique ID, dense search, BM25, công thức RRF, fallback theo dense score, fuse đúng một lần và xử lý lỗi provider.
- `pytest tests/test_acceptance.py -q`: **5/5 passed**; corpus đủ 3 legal + 5 news, dữ liệu chuẩn hóa đủ hai loại, golden dataset đủ 15 case và evaluation report không còn placeholder.
- `pytest -q`: **20/20 passed**; test suite không gọi API/network thật.
- A/B retrieval: hybrid + RRF tốt hơn dense-only ở cả 4 metric; faithfulness `+0.0683`, answer relevance `+0.0512`, context recall `+0.2000`, context precision `+0.0448`.
- Query hiệu chỉnh đã ghi nhận: in-domain có best dense cosine khoảng `0.62`, out-of-domain khoảng `0.32`; vùng threshold hợp lý khoảng `0.45`.

## Điều còn hạn chế

- `SCORE_THRESHOLD` hiện vẫn là `0.3`, thấp hơn vùng hiệu chỉnh khoảng `0.45`; đồng thời PageIndex chưa được nhóm triển khai. Vì vậy fallback hiện chủ yếu bảo đảm không crash, chưa chứng minh được chất lượng truy xuất vectorless.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện là chốt threshold bằng tập validation riêng, sau đó lọc BM25 score thấp hoặc thêm cross-encoder sau RRF để giảm chunk nhiễu mà vẫn giữ mức recall đã đạt.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 2026-09-20
- Tên thành viên: Vũ Thường Tín
