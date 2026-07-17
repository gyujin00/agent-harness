# ai/

`ai-worker` 전용 작업 공간 (`harness/permissions.policy.md`: 쓰기 허용, `ai/prompts/` 포함).

- 목표: 기능 추가가 아니라 **eval 점수 회귀 방지/개선** (`../eval/`).
- 실행 루프: [`../loops/ai.loop.yaml`](../loops/ai.loop.yaml)
- verify: `../eval/run-eval.py` 실행 → `../eval/thresholds.yaml` 기준선 비교 — `verifier`가 판정.
- 임베딩 모델·청크 전략·Top-K 변경은 ADR 필수 (`../docs/decisions/`).

## T-001 (FR-017 FAQ RAG) — 구현됨

실제 OpenAI API를 호출하는 RAG 파이프라인이 여기 구현되어 있다 (`../docs/decisions/ADR-006-*.md`
계승). 모듈:

- `corpus.py` — `../requirements/prd.md` + `../requirements/frd.md`를 512자/64자 overlap으로
  결정론적 청킹(`corpus/chunks.json` 캐시, git 커밋 대상 — 사람이 눈으로 확인 가능).
- `embeddings.py` — `text-embedding-3-small`로 청크/질의 임베딩 (`corpus/embeddings.npy` 캐시,
  git 커밋 **제외** — `.gitignore` 참고. 실제 API 호출 비용이 드는 파생 데이터라 재실행으로
  재생성한다).
- `retrieval.py` — top_k=5, 실제 MMR(maximal marginal relevance) 구현 (plain top-k 아님).
- `generation.py` — `gpt-4o-mini`로 답변 생성. 프롬프트는 `prompts/faq_answer.md`.
- `scoring.py` — eval의 `score_faithfulness`(LLM judge)/`score_answer_relevancy`(임베딩
  코사인 유사도) 구현.
- `pipeline.py` — 위를 엮은 `run_pipeline()`. BR-007 "근거 없음" 게이트를 2단계로 구현
  (모듈 docstring 참고) — 1차: LLM이 검색된 컨텍스트가 실제로 질문을 뒷받침하는지 직접 판단해
  `NO_EVIDENCE` sentinel 출력(주 메커니즘), 2차: 명백히 무관한 질의에 대한 저비용 유사도 하한
  (비용 절감용, BR-007 판단의 주 근거 아님).

`../eval/run-eval.py`의 `run_pipeline`/`score_faithfulness`/`score_answer_relevancy`는 더 이상
`NotImplementedError` 스텁이 아니다. ai-worker는 이 스크립트를 스스로 실행해 통과를 선언하지
않는다(work ≠ verify) — 개발 중 크래시 여부 확인용으로만 실행했다.
