"""
Đánh giá A/B: Config A (dense-only) vs Config B (hybrid + RRF).

Chỉ thay retrieval strategy (use_reranking); giữ nguyên golden dataset,
generator, evaluator, prompt và top_k. Tính 4 metric bằng ragas:
faithfulness, answer_relevancy, context_recall, context_precision.

Chạy:  python -m scripts.evaluate_rag
Kết quả số liệu lưu tại group_project/evaluation/eval_output.json
"""

import json
import time
from pathlib import Path

from dotenv import load_dotenv

from src.task9_retrieval_pipeline import retrieve, SCORE_THRESHOLD
from src.task10_generation import (
    SYSTEM_PROMPT,
    TOP_K,
    LLM_MODEL,
    call_llm,
    format_context,
    reorder_for_llm,
)
from src.task4_chunking_indexing import EMBEDDING_MODEL

from ragas import EvaluationDataset, SingleTurnSample, evaluate
from ragas.metrics import (
    Faithfulness,
    ResponseRelevancy,
    LLMContextRecall,
    LLMContextPrecisionWithReference,
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


load_dotenv()

ROOT = Path(__file__).parent.parent
EVAL_DIR = ROOT / "group_project" / "evaluation"
GOLDEN = EVAL_DIR / "golden_dataset.json"
OUTPUT = EVAL_DIR / "eval_output.json"

EVALUATOR_MODEL = "gpt-4o-mini"
GENERATOR_MODEL = LLM_MODEL.strip() or "gpt-4o-mini"

CONFIGS = {
    "A_dense_only": {"use_reranking": False},
    "B_hybrid_rrf": {"use_reranking": True},
}


def generate(query: str, use_reranking: bool) -> tuple[str, list[str]]:
    """Sinh câu trả lời với retrieval strategy cho trước; giữ prompt/generator cố định."""
    chunks = retrieve(query, top_k=TOP_K, use_reranking=use_reranking)
    if not chunks:
        return "Tôi không thể xác minh thông tin này từ nguồn hiện có.", []
    context = format_context(reorder_for_llm(chunks))
    user_message = f"Context:\n{context}\n\nQuestion: {query}"
    try:
        answer = call_llm(SYSTEM_PROMPT, user_message)
    except Exception as error:  # provider lỗi -> không crash eval
        answer = f"[generation error] {error}"
    return answer, [chunk["content"] for chunk in chunks]


def build_samples(golden: list[dict], use_reranking: bool) -> tuple[EvaluationDataset, list[float]]:
    samples, latencies = [], []
    for case in golden:
        start = time.perf_counter()
        answer, contexts = generate(case["question"], use_reranking)
        latencies.append(time.perf_counter() - start)
        samples.append(
            SingleTurnSample(
                user_input=case["question"],
                response=answer,
                retrieved_contexts=contexts,
                reference=case["expected_answer"],
                reference_contexts=[case["expected_context"]],
            )
        )
    return EvaluationDataset(samples=samples), latencies


def main() -> None:
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    print(f"Golden dataset: {len(golden)} cases")

    evaluator_llm = LangchainLLMWrapper(ChatOpenAI(model=EVALUATOR_MODEL, temperature=0))
    evaluator_emb = LangchainEmbeddingsWrapper(OpenAIEmbeddings(model=EMBEDDING_MODEL))
    metrics = [
        Faithfulness(),
        ResponseRelevancy(),
        LLMContextRecall(),
        LLMContextPrecisionWithReference(),
    ]

    report = {
        "run_info": {
            "generator_model": GENERATOR_MODEL,
            "evaluator_model": EVALUATOR_MODEL,
            "embedding_model": EMBEDDING_MODEL,
            "top_k": TOP_K,
            "score_threshold": SCORE_THRESHOLD,
            "golden_dataset_size": len(golden),
        },
        "configs": {},
    }

    for name, cfg in CONFIGS.items():
        print(f"\n=== Config {name} (use_reranking={cfg['use_reranking']}) ===")
        dataset, latencies = build_samples(golden, cfg["use_reranking"])
        result = evaluate(dataset=dataset, metrics=metrics, llm=evaluator_llm, embeddings=evaluator_emb)
        df = result.to_pandas()

        metric_cols = [c for c in df.columns if c in
                       {"faithfulness", "answer_relevancy", "context_recall",
                        "llm_context_precision_with_reference"}]
        overall = {col: round(float(df[col].mean()), 4) for col in metric_cols}
        overall["avg_latency_s"] = round(sum(latencies) / len(latencies), 3)

        per_case = []
        for i, row in df.iterrows():
            per_case.append({
                "question": golden[i]["question"],
                **{col: (round(float(row[col]), 4) if row[col] == row[col] else None) for col in metric_cols},
                "latency_s": round(latencies[i], 3),
            })

        report["configs"][name] = {"overall": overall, "per_case": per_case}
        print("overall:", overall)

    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved: {OUTPUT}")


if __name__ == "__main__":
    main()
