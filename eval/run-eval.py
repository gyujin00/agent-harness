"""eval/run-eval.py — RAG verify 하네스

verifier sub-agent가 ai.loop.yaml의 verify 단계에서 호출한다.
정답셋(rag-eval-set.jsonl)으로 파이프라인을 돌려 점수를 내고,
thresholds.yaml 기준선과 비교해 pass/fail을 판정한다.

T-001에서 실제 RAG 파이프라인/스코어러(ai/pipeline.py, ai/scoring.py)를 연결했다
(더 이상 NotImplementedError 스텁이 아니다). 이 파일 자체의 통제 흐름
(로드→평가→기준선 비교→리포트)은 ai-worker가 바꾸지 않았다 — verifier/orchestrator 소유.

주의: ai-worker는 이 스크립트를 스스로 실행해 "통과"를 선언하지 않는다(work ≠ verify,
harness/verification.policy.md). 개발 중 크래시 여부 확인 목적의 실행만 했다 — 공식 판정은
verifier가 한다.
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

# ai/ lives at the repo root, one level up from eval/ -- add repo root to
# sys.path so `from ai... import ...` resolves regardless of whether this
# script is invoked as `python eval/run-eval.py` (script dir on sys.path is
# eval/, not repo root) or via `python -m eval.run-eval` from repo root.
_REPO_ROOT = ROOT.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


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


# ── 실제 파이프라인 연결 지점 (ai/pipeline.py, ai/scoring.py) ──────
from ai.pipeline import run_pipeline  # noqa: E402  (FR-017 RAG: retrieve + generate, incl. BR-007 no-evidence gate)
from ai.scoring import score_faithfulness, score_answer_relevancy  # noqa: E402  (LLM-judge / embedding-cosine scorers, see ai/scoring.py docstring)


def score_retrieval_at_k(retrieved: list[str], gold: list[str], k: int) -> float:
    hit = any(cid in retrieved[:k] for cid in gold)
    return 1.0 if hit else 0.0
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
