# RAG evaluation results

## Run information

| Field                              | Value |
| ---------------------------------- | ----- |
| Evaluation date                    | 2026-09-20 |
| Framework and version              | ragas 0.4.3 |
| Evaluator model                    | gpt-4o-mini (temperature=0) |
| Generator model                    | gpt-4o-mini |
| Embedding model                    | text-embedding-3-small (1536d) |
| Corpus version/commit              | a65f14b |
| Golden dataset size                | 15 |
| `top_k`                            | 5 |
| Fallback threshold and calibration | SCORE_THRESHOLD = 0.3. Hiệu chỉnh bằng query in-domain (best dense cosine ≈ 0.62) và out-of-domain (≈ 0.32); ngưỡng hợp lý ~0.45. Vì nhóm không dùng PageIndex, fallback chỉ ảnh hưởng tín hiệu refusal, không đổi kết quả retrieval. |

## Configurations

- **Config A — dense-only:** `retrieve(query, top_k=5, use_reranking=False)` → trả `semantic_search` (ChromaDB cosine, text-embedding-3-small) cắt top_k.
- **Config B — hybrid + RRF:** `retrieve(query, top_k=5, use_reranking=True)` → fuse `semantic_search` + `lexical_search` (BM25) bằng Reciprocal Rank Fusion (k=60).

Hai config dùng cùng golden dataset, generator (gpt-4o-mini), evaluator (gpt-4o-mini), prompt (`SYSTEM_PROMPT`) và `top_k=5`; chỉ thay retrieval strategy. Script: `scripts/evaluate_rag.py`; số liệu thô: `group_project/evaluation/eval_output.json`.

## Overall scores

| Metric            | Config A | Config B | Delta B−A |
| ----------------- | -------: | -------: | --------: |
| Faithfulness      |   0.8333 |   0.9016 |   +0.0683 |
| Answer relevance  |   0.5165 |   0.5677 |   +0.0512 |
| Context recall    |   0.7333 |   0.9333 |   +0.2000 |
| Context precision |   0.8100 |   0.8548 |   +0.0448 |
| **Average**       |   0.7233 |   0.8144 |   +0.0911 |

Latency trung bình/câu (gồm cả generation, biến động theo API): Config A ≈ 5.24s, Config B ≈ 3.70s.

## A/B comparison

- **Cấu hình tốt hơn:** Config B (hybrid + RRF) — thắng ở **cả 4 metric**.
- **Evidence:** Cải thiện lớn nhất ở **context recall (+0.20)** — BM25 bổ sung các chunk khớp từ khóa/số hiệu mà dense bỏ sót, giúp RRF đẩy đúng bằng chứng lên top_k. Faithfulness (+0.068) và precision (+0.045) cũng tăng vì context đưa vào generation sát hơn. Không có case quan trọng nào bị mất bằng chứng khi chuyển từ A sang B (không metric tổng nào của B tụt dưới A).
- **Trade-off về latency/cost:** Config B thêm một bước BM25 (chạy **local, không tốn API**) và một lần RRF (O(n log n) trên ứng viên top_k×2) — chi phí không đáng kể. Latency đo được của B còn thấp hơn A, nhưng con số này gồm cả thời gian gọi LLM generation nên nhiễu; **không dùng để kết luận B nhanh hơn A** — kết luận đúng là overhead retrieval của B là nhỏ. Cost API mỗi câu của A và B tương đương (cùng 1 embed query + 1 generation).

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------- | ---------- |
|   1 | Quỹ học bổng cho HS khó khăn của ĐHBK trị giá bao nhiêu? (case #8) | B | 0.00 | 0.56 | 1.00 | 0.50 | generation | Answer đúng ("45 tỷ") và context có đủ bằng chứng (recall=1), nhưng câu trả lời trích dẫn `[Document 5]` trong khi bằng chứng "45 tỷ" nằm ở tài liệu khác. `reorder_for_llm` xáo trộn thứ tự Document nên số citation model gán bị lệch → evaluator chấm claim không được support → faithfulness=0. |
|   2 | Nghị định nào quy định học bổng ngành KH cơ bản? (case #11) | B | 1.00 | 0.49 | 0.00 | 0.95 | retrieval / data | Answer đúng ("179/2026/NĐ-CP") nhưng 5 chunk lấy được đều là **nội dung điều khoản**, không chunk nào chứa **số hiệu** "179/2026/NĐ-CP" (số hiệu nằm ở header/chunk-0, phần OCR nhiễu). Reference chứa số hiệu → context_recall=0. Chunking tách số hiệu khỏi nội dung. |
|   3 | Mức học bổng chương trình tài năng theo NĐ179? (case #5) | B | 1.00 | 0.67 | 1.00 | 0.50 | retrieval | Precision B (0.50) thấp hơn A (1.00): RRF kéo thêm chunk `nghi-dinh-179 chunk-24` (khớp từ khóa "179/2026", "sinh viên" nhưng **không chứa mức 5.5tr**) vào top_k → nhiễu. Đây là trade-off của fusion: tăng recall tổng nhưng đôi khi giảm precision ở case đơn lẻ. |

Ghi chú: **answer relevance thấp đồng đều ở cả A và B (~0.5)**. Mở từng case cho thấy câu trả lời *đúng* nhưng rất ngắn và có chèn chuỗi `(Document N)`; ragas answer_relevancy sinh câu hỏi ngược từ answer rồi so embedding — answer ngắn/kèm nhiễu citation làm điểm này tụt. Đây là tín hiệu ở **tầng generation/định dạng answer**, không phải retrieval (vì cả hai config đều thấp như nhau).

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
| 1 | Ổn định citation: đánh nhãn Document **trước** `reorder_for_llm`, hoặc trích dẫn theo `source/title` thay vì số thứ tự Document | Case #8: faithfulness=0 do citation lệch sau reorder | Faithfulness case #8 và tổng thể tăng | Chạy lại `scripts/evaluate_rag.py`, kiểm faithfulness case #8 > 0 và average faithfulness tăng |
| 2 | Prepend tiêu đề tài liệu (đã chứa số hiệu nghị định) vào đầu mỗi chunk khi index ở Task 4 | Case #11: recall=0 vì chunk nội dung không chứa số hiệu "179/2026/NĐ-CP" | Context recall các câu hỏi "nghị định nào" tăng; giảm nhầm nguồn | Re-index rồi chạy lại eval; kiểm context_recall case #11 > 0 |
| 3 | Giảm nhiễu RRF: lọc chunk BM25 có score quá thấp trước khi fuse, hoặc thêm reranker (Jina/cross-encoder) sau RRF | Case #5: precision B (0.50) < A (1.00) do chunk BM25 nhiễu lọt top_k | Context precision của B tăng, giữ nguyên recall | Chạy lại eval sau khi thêm bước lọc/rerank; so precision B trước–sau |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| (Chưa chạy) Rerank Jina/cross-encoder sau RRF | Config B (RRF) | Sẽ đo sau khi chạy | Sẽ đo sau khi chạy | Kỳ vọng cải thiện precision (xem Recommendation #3); là bonus, chưa bắt buộc |
