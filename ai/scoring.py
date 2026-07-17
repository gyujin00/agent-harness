"""ai/scoring.py — real faithfulness / answer-relevancy scorers for FR-017 eval.

Wired into eval/run-eval.py's score_faithfulness / score_answer_relevancy.
Neither of these is a stub -- both make real OpenAI API calls (or reuse the
embedding cache) and produce a genuine 0.0-1.0 score.

## score_faithfulness — LLM judge (gpt-4o-mini)

Prompt: ai/prompts/faithfulness_judge.md. Given the answer + the actual text
of the retrieved chunks, the judge rates how well the answer is grounded in
(not going beyond) that context.

Special case (BR-007 regression sample): when `retrieved` is empty, there's
no context to judge groundedness against. This happens exactly when
ai/pipeline.py's no-evidence gate triggered. In that situation:
  - if the answer is the fixed ADR-007 fallback text -> the pipeline
    correctly declined to answer without evidence, which is *maximally*
    faithful behavior (it asserted nothing ungrounded) -> score 1.0.
  - if the answer is anything else with zero retrieved evidence -> that
    would mean the pipeline answered without any grounding at all, i.e. a
    hallucination -> score 0.0.
This is not score-gaming: it's scoring the actual faithfulness property
(did the system assert anything not backed by evidence?) for the one case
where there's no chunk text to run the LLM judge against.

## score_answer_relevancy — embedding cosine similarity

cosine_similarity(embed(answer), embed(expected_answer)), reusing
ai/embeddings.embed_query (same text-embedding-3-small model already paid
for/cached for retrieval -- no new infra). No special-casing needed here:
eval/rag-eval-set.jsonl's BR-007 regression sample sets `expected_answer`
to (near-)exactly the ADR-007 fallback text, so a correctly-triggered
fallback naturally scores near 1.0 by plain embedding similarity, and an
incorrect refusal-when-answerable or answer-when-should-refuse naturally
scores low -- the eval-set authoring choice does the special-casing, not
the scorer code.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import numpy as np

from ai.corpus import chunks_by_id
from ai.embeddings import embed_query
from ai.generation import FALLBACK_TEXT, LLM_MODEL

JUDGE_PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "faithfulness_judge.md"

_client = None
_JUDGE_SYSTEM_PROMPT: str | None = None


def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set in the environment. "
                "This scorer calls the real OpenAI API (docs/decisions/ADR-006) and does not fall back to a mock."
            )
        _client = OpenAI(api_key=api_key)
    return _client


def _load_judge_prompt() -> str:
    global _JUDGE_SYSTEM_PROMPT
    if _JUDGE_SYSTEM_PROMPT is not None:
        return _JUDGE_SYSTEM_PROMPT
    raw = JUDGE_PROMPT_PATH.read_text(encoding="utf-8")
    m = re.search(r"## System Prompt\s*\n\n(.*?)\n\n## User Prompt", raw, re.DOTALL)
    if not m:
        raise RuntimeError(f"could not find '## System Prompt' section in {JUDGE_PROMPT_PATH}")
    _JUDGE_SYSTEM_PROMPT = m.group(1).strip()
    return _JUDGE_SYSTEM_PROMPT


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-12
    return float(np.dot(a, b) / denom)


def _parse_score(text: str) -> float:
    m = re.search(r"[-+]?\d*\.?\d+", text)
    if not m:
        raise ValueError(f"faithfulness judge did not return a parseable number: {text!r}")
    value = float(m.group(0))
    return max(0.0, min(1.0, value))


def score_faithfulness(answer: str, retrieved: list[str]) -> float:
    if not retrieved:
        # No-evidence case (ai/pipeline.py gate triggered). See module docstring.
        return 1.0 if answer.strip() == FALLBACK_TEXT.strip() else 0.0

    by_id = chunks_by_id()
    context = "\n\n".join(f"[{cid}] {by_id[cid].text}" for cid in retrieved if cid in by_id)

    client = _get_client()
    system_prompt = _load_judge_prompt()
    user_prompt = (
        f"근거 문서 조각:\n{context}\n\n생성된 답변:\n{answer}\n\n"
        "위 답변의 충실도(faithfulness) 점수를 0.0~1.0 사이 숫자 하나로만 출력하세요."
    )
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    raw = (resp.choices[0].message.content or "").strip()
    return _parse_score(raw)


def score_answer_relevancy(answer: str, expected: str) -> float:
    a_vec = np.array(embed_query(answer), dtype=np.float32)
    e_vec = np.array(embed_query(expected), dtype=np.float32)
    sim = _cosine(a_vec, e_vec)
    # cosine similarity for embeddings is already effectively in [~0,1] for
    # same-language same-domain text pairs, but clamp defensively.
    return max(0.0, min(1.0, sim))
