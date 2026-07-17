"""eval/run-eval.py — RAG verify 하네스 뼈대

verifier sub-agent가 rag.loop.yaml의 verify 단계에서 호출한다.
정답셋(rag-eval-set.jsonl)으로 파이프라인을 돌려 점수를 내고,
thresholds.yaml 기준선과 비교해 pass/fail을 판정한다.

TODO로 표시된 부분에 실제 RAG 파이프라인/스코어러를 연결하세요.
이 파일은 통제 흐름(로드→평가→기준선 비교→리포트)만 고정합니다.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml  # pip install pyyaml

ROOT = Path(__file__).resolve().parent
EVAL_SET = ROOT / "rag-eval-set.jsonl"
THRESHOLDS = ROOT / "thresholds.yaml"


@dataclass
class Sample:
    id: str
    question: str
    expected_answer: str
    gold_chunk_ids: list[str]


def load_eval_set(path: Path) -> list[Sample]:
    samples = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        samples.append(Sample(d["id"], d["question"], d["expected_answer"], d["gold_chunk_ids"]))
    return samples


# ── TODO: 실제 파이프라인 연결 지점 ───────────────────────────────
def run_pipeline(question: str) -> tuple[list[str], str]:
    """질문 → (검색된 chunk_id 목록, 생성된 답변)을 반환하도록 구현하세요."""
    raise NotImplementedError("ai/ 의 RAG 파이프라인을 여기에 연결하세요")


def score_retrieval_at_k(retrieved: list[str], gold: list[str], k: int) -> float:
    hit = any(cid in retrieved[:k] for cid in gold)
    return 1.0 if hit else 0.0


def score_faithfulness(answer: str, retrieved: list[str]) -> float:
    raise NotImplementedError("근거 기반 충실도 스코어러를 연결하세요")


def score_answer_relevancy(answer: str, expected: str) -> float:
    raise NotImplementedError("답변 적합도 스코어러를 연결하세요")
# ──────────────────────────────────────────────────────────────


def main() -> int:
    thresholds = yaml.safe_load(THRESHOLDS.read_text(encoding="utf-8"))
    k = thresholds["config"]["top_k"]
    samples = load_eval_set(EVAL_SET)

    agg = {"retrieval_at_k": 0.0, "faithfulness": 0.0, "answer_relevancy": 0.0}
    for s in samples:
        retrieved, answer = run_pipeline(s.question)
        agg["retrieval_at_k"] += score_retrieval_at_k(retrieved, s.gold_chunk_ids, k)
        agg["faithfulness"] += score_faithfulness(answer, retrieved)
        agg["answer_relevancy"] += score_answer_relevancy(answer, s.expected_answer)

    n = len(samples)
    scores = {m: round(v / n, 4) for m, v in agg.items()}

    failed = []
    for metric, value in scores.items():
        floor = thresholds[metric]
        mark = "PASS" if value >= floor else "FAIL"
        if value < floor:
            failed.append(metric)
        print(f"[{mark}] {metric:18s} {value:.4f}  (기준선 {floor})")

    if failed:
        print(f"\nVERIFY FAILED: {', '.join(failed)} — action으로 되돌립니다.")
        return 1
    print("\nVERIFY PASSED — record 단계로 진행합니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
