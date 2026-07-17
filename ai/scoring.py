"""ai/scoring.py — real faithfulness / answer-relevancy scorers for FR-017 eval.

Wired into eval/run-eval.py's score_faithfulness / score_answer_relevancy.
Neither of these is a stub -- both make real OpenAI API calls and produce a
genuine 0.0-1.0 score.

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

## score_answer_relevancy — LLM judge (gpt-4o-mini), question vs. answer

T-001 code review finding: the original implementation was
`cosine(embed(answer), embed(expected_answer))`. That measures "does this
answer's wording resemble one fixed reference string", not "does this
answer address the question" -- a metric-design problem, not a phrasing
nitpick (all 9 eval-set answers were independently judged fully correct and
faithful, yet several scored low on that metric purely for using different,
equally-correct vocabulary than the hand-written `expected_answer`, e.g.
"사유가 안내된다" vs "기존 업체 정보가 안내됩니다").

Replaced with an LLM judge (ai/prompts/relevancy_judge.md) that's given the
*question* and the *answer* -- explicitly NOT the expected_answer as a
ground truth to match wording against -- and asked whether the answer
actually addresses what was asked. eval/run-eval.py's main() was changed
minimally at one call site (score_answer_relevancy(answer, s.expected_answer)
-> score_answer_relevancy(s.question, answer)) to plumb the question
through; no loop/branch/threshold logic in main() was touched.

Symmetric no-evidence handling with score_faithfulness (code review
Important #3): score_answer_relevancy has its own explicit branch, keyed on
the answer being exactly ai.generation.FALLBACK_TEXT -- not on eval-set
wording happening to resemble it. A correctly-triggered BR-007 fallback is,
by definition, the maximally relevant response to a question with no
evidence in the corpus. A pipeline that incorrectly declines on an
answerable question is still caught by retrieval_at_k (retrieved=[] misses
the gold chunk), so this branch doesn't mask that failure mode from the
aggregate score.
"""
from __future__ import annotations

import re
from pathlib import Path

from ai.corpus import chunks_by_id
from ai.generation import FALLBACK_TEXT, LLM_MODEL
from ai.llm_client import get_client, load_prompt_section

FAITHFULNESS_PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "faithfulness_judge.md"
RELEVANCY_PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "relevancy_judge.md"

_FAITHFULNESS_SYSTEM_PROMPT: str | None = None
_RELEVANCY_SYSTEM_PROMPT: str | None = None


def _load_faithfulness_prompt() -> str:
    global _FAITHFULNESS_SYSTEM_PROMPT
    if _FAITHFULNESS_SYSTEM_PROMPT is None:
        _FAITHFULNESS_SYSTEM_PROMPT = load_prompt_section(FAITHFULNESS_PROMPT_PATH, "System Prompt")
    return _FAITHFULNESS_SYSTEM_PROMPT


def _load_relevancy_prompt() -> str:
    global _RELEVANCY_SYSTEM_PROMPT
    if _RELEVANCY_SYSTEM_PROMPT is None:
        _RELEVANCY_SYSTEM_PROMPT = load_prompt_section(RELEVANCY_PROMPT_PATH, "System Prompt")
    return _RELEVANCY_SYSTEM_PROMPT


def _parse_score(text: str) -> float:
    m = re.search(r"[-+]?\d*\.?\d+", text)
    if not m:
        raise ValueError(f"judge did not return a parseable number: {text!r}")
    value = float(m.group(0))
    return max(0.0, min(1.0, value))


def _judge(system_prompt: str, user_prompt: str) -> float:
    client = get_client()
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


def score_faithfulness(answer: str, retrieved: list[str]) -> float:
    if not retrieved:
        # No-evidence case (ai/pipeline.py gate triggered). See module docstring.
        return 1.0 if answer.strip() == FALLBACK_TEXT.strip() else 0.0

    by_id = chunks_by_id()
    context = "\n\n".join(f"[{cid}] {by_id[cid].text}" for cid in retrieved if cid in by_id)
    user_prompt = (
        f"근거 문서 조각:\n{context}\n\n생성된 답변:\n{answer}\n\n"
        "위 답변의 충실도(faithfulness) 점수를 0.0~1.0 사이 숫자 하나로만 출력하세요."
    )
    return _judge(_load_faithfulness_prompt(), user_prompt)


def score_answer_relevancy(question: str, answer: str) -> float:
    """LLM-judge relevancy: does `answer` actually address `question`?

    See module docstring for why this replaced embed(answer)-vs-
    embed(expected_answer) cosine similarity, and for the explicit
    no-evidence branch below (code review Important #3).
    """
    if answer.strip() == FALLBACK_TEXT.strip():
        return 1.0

    user_prompt = (
        f"질문:\n{question}\n\n답변:\n{answer}\n\n"
        "위 답변이 이 질문에 실제로 답하고 있는 정도(relevancy)를 0.0~1.0 사이 숫자 하나로만 출력하세요."
    )
    return _judge(_load_relevancy_prompt(), user_prompt)
