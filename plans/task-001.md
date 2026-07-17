# Task-001: FAQ RAG 파이프라인 구현 + corpus 구축 (FR-017)

- Sprint: sprint-01
- 도메인: ai
- 실행 loop: loops/ai.loop.yaml
- 상태: in_progress
- worker: ai-worker (permissions.policy.md 범위 내: `ai/`, `ai/prompts/` 쓰기)

## 목적
Sprint-01 목표(FAQ/RAG 1회전 실증)를 달성하기 위한 실제 구현 Task. FR-017("평가 기준에 대한 문의에
FAQ 기능으로 답변")을 저장된 근거 문서 검색 기반으로 구현하고, BR-007 가드레일(근거 없이 답변 생성
금지)이 실제로 지켜지는지 eval로 검증한다.

## 범위 (Scope)
- 건드리는 경로: `ai/`, `ai/prompts/` (ai-worker 쓰기 권한 범위)
- 다루는 것: corpus 구축(`requirements/prd.md` + `requirements/frd.md`를 청킹해 인덱싱), 임베딩
  (OpenAI `text-embedding-3-small`, `eval/thresholds.yaml` 기준), 검색(top_k=5, mmr), 답변 생성
  (OpenAI `gpt-4o-mini`), "근거 없음" 폴백 처리.
- 건드리지 않는 것: `backend/`, `frontend/`, FR-016·018·019·020(다른 FR, 별도 Task), FR-014(합성
  데이터 시딩, 별도 Sprint 후보).

## 기준 문서 (반드시 확인)
- 프로젝트 헌법: `AGENTS.md`
- 요구사항: `requirements/frd.md` FR-017, BR-007, BR-009, DATA-012/013, §7 AI(FR-017 판단), OQ-006/OQ-010
- AI 도메인: `eval/thresholds.yaml`(기준선·config), `eval/rag-eval-set.jsonl`(정답셋 — 이 Task 중
  SRM 더미 문항을 corpus 기반 실제 문항으로 교체), `docs/decisions/ADR-006-*.md`(실제 API 계승 근거)

## Definition of Done (verify 통과 조건)
- `loops/ai.loop.yaml`의 verify.gates 전부 통과: retrieval@k ≥ 0.80, faithfulness ≥ 0.85,
  answer_relevancy ≥ 0.80 (`eval/thresholds.yaml` 기준선)
- `eval/run-eval.py`의 `run_pipeline`/`score_faithfulness`/`score_answer_relevancy` TODO가 실제
  구현으로 대체돼 있다(더 이상 NotImplementedError를 던지지 않는다)
- 근거 문서가 없는 질문에 답변을 생성하지 않고 "근거 없음"을 반환하는 케이스가 eval-set에 최소
  1건 포함돼 통과한다(BR-007 회귀 방지)
- self-eval 없음: ai-worker는 eval을 스스로 돌려 통과 판정하지 않는다(verifier가 판정)

## 산출물 (record)
- PR, `ai/` 구현 코드, `ai/prompts/` 프롬프트, eval 리포트(before/after — before는 NotImplementedError
  로 실행 불가했던 상태)
- traceability: `docs/traceability.md`에 FR-017 → sprint-01/T-001 → 코드/PR → eval 결과 행 추가

## 변경 발생 시
- 임베딩 모델·청크 전략·Top-K·retriever 변경은 ADR 필수(ai-worker.spec.md 결정 규약).
- OQ-010(FAQ 폴백)이 이 Task 도중 확정되지 않으면, 코드를 지어내지 말고 임시 고정 응답으로 구현하고
  ADR-proposed + Human PM 에스컬레이션을 병행한다(sprint-01.md Open Issues 참고). 임의로 폴백 규칙을
  확정하지 않는다.
