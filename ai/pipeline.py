"""ai/pipeline.py — end-to-end FR-017 FAQ RAG pipeline, wired into
eval/run-eval.py's run_pipeline().

## "No evidence" detection (BR-007) — two layers, and why

The task allowed picking either (a) a similarity-score threshold, or (b) an
LLM sentinel. During development (see commit message / T-001 report) I
measured real query→top-1-cosine-similarity scores against the built
corpus (ai/corpus/chunks.json, 139 chunks over PRD+FRD):

  - clearly relevant SRM questions (grading, low-performer criteria,
    registration flow):                        top-1 sim ~0.40-0.53
  - clearly off-topic questions (weather, food): top-1 sim ~0.18-0.31
  - SRM-***adjacent but out-of-scope*** questions (e.g. "실시간 ERP 연동은
    어떻게 처리되나요?", "계약서 작성/발주 절차는?") scored top-1 sim
    ~0.42-00.44 — INSIDE the "relevant" band, because the corpus explicitly
    lists these as Out of Scope, giving high lexical/semantic overlap with
    the query despite the passage containing zero actual answer.

A single similarity threshold can't distinguish "the top chunk answers this"
from "the top chunk merely uses the same words to say we don't do this" —
so a pure mechanism (a) gate would let the LLM treat "out of scope" text as
if it were grounding, and answer anyway. That's exactly what BR-007 exists
to prevent (real content, but not real "answer support"). So:

  - PRIMARY gate = mechanism (b): the LLM itself judges, per-chunk-content,
    whether the retrieved context actually supports an answer (see
    ai/prompts/faq_answer.md rule 3, ai/generation.py NO_EVIDENCE_SENTINEL).
  - SECONDARY, cheap pre-filter = a conservative low similarity floor
    (NOISE_FLOOR below) that skips the LLM call entirely only for queries
    so far off-topic that no SRM-adjacent question in testing ever scored
    that low. This exists purely to save an API call on obvious noise, not
    to make the "is this really no-evidence" judgment — that call is
    entirely mechanism (b)'s.
"""
from __future__ import annotations

from ai.generation import FALLBACK_TEXT, generate_answer
from ai.retrieval import TOP_K, retrieve

# Empirically, no SRM-domain-adjacent question (even out-of-scope ones like
# ERP integration / contract renewal) scored below ~0.31 top-1 cosine
# similarity, while genuinely unrelated queries (weather, recipes) scored
# ~0.18-0.30. This floor is intentionally conservative (well below the
# lowest adjacent-but-real-topic score observed) so it only ever fires on
# unambiguous noise -- it is a cost-saving short-circuit, not the BR-007
# decision boundary (see module docstring).
NOISE_FLOOR = 0.22


def run_pipeline(question: str, top_k: int = TOP_K) -> tuple[list[str], str]:
    """FR-017 FAQ RAG: question -> (retrieved_chunk_ids, answer).

    retrieved_chunk_ids is [] whenever the no-evidence fallback triggers
    (either gate) -- this is a deliberate signal to eval/run-eval.py's
    scorers (see ai/scoring.py) that "no evidence was used" rather than
    "evidence was used but the retrieval@k metric happened to miss the
    gold chunk".
    """
    hits = retrieve(question, top_k=top_k)

    if not hits or hits[0].score < NOISE_FLOOR:
        return [], FALLBACK_TEXT

    answer = generate_answer(question, hits)

    if answer == FALLBACK_TEXT:
        # The LLM emitted the NO_EVIDENCE sentinel (ai/generation.py already
        # translated it to FALLBACK_TEXT) -- report no chunks as "used".
        return [], FALLBACK_TEXT

    return [h.chunk_id for h in hits], answer


if __name__ == "__main__":
    import sys

    q = sys.argv[1] if len(sys.argv) > 1 else "공급업체 등급은 어떻게 산정되나요?"
    ids, answer = run_pipeline(q)
    print("question:", q)
    print("retrieved:", ids)
    print("answer:", answer)
