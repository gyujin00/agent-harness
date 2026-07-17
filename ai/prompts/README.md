# ai/prompts/

RAG 파이프라인이 사용하는 프롬프트 템플릿을 둔다. 프롬프트 변경은
`loops/ai.loop.yaml`의 signal 트리거(`prompt 변경 → 회귀 평가`) 대상이다.

- `faq_answer.md` — FAQ 답변 생성 프롬프트 (`ai/generation.py`). BR-007 "근거 없음" 감지
  메커니즘(LLM sentinel `NO_EVIDENCE`)이 규칙 3번으로 들어있다.
- `faithfulness_judge.md` — eval의 faithfulness LLM-judge 프롬프트 (`ai/scoring.py`).
