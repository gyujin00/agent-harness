# Sprint-01: FAQ/RAG(FR-017) 1회전 실증

- 상태: active
- Phase/Scope: AI 워크스트림 첫 기능. "막힌 것 빼고는 자동 진행, 규칙 미정은 ADR+에스컬레이션"
  통제 모델(a→b→c 사이클)을 FR-017 하나로 실제로 완주시킨다. 완성도가 아니라 통제 과정 실증이 목표.
- 관련 기준 문서: `AGENTS.md`, `requirements/frd.md`(FR-017, BR-007, BR-009, DATA-012/013, OQ-006/OQ-010),
  `docs/decisions/ADR-006-*.md`(실제 OpenAI API 계승), `harness/verification.policy.md`,
  `eval/thresholds.yaml`

## 목표 (Goal)
- 사용자가 평가 기준(품질/납기/가격/대응력)에 대해 자연어로 질문하면, `ai/` RAG 파이프라인이
  근거 문서(corpus: `requirements/prd.md` + `requirements/frd.md`, 확장 시 ADR로 근거 추가)를
  검색해 실제 OpenAI API(Embedding + Chat Completions)로 답변을 생성한다.
- 근거 문서가 없거나 검색 결과가 없으면 답변을 생성하지 않고 "근거 없음"을 표시한다(FR-017/BR-007
  가드레일 — 환각 방지가 이 Sprint의 핵심 검증 대상).
- `eval/run-eval.py`가 이 파이프라인을 실제로 호출해 retrieval@k·faithfulness·answer_relevancy를
  `eval/thresholds.yaml` 기준선과 비교, verifier가 판정하는 전체 loop 1회전을 실증한다.

## 완료 조건 (Definition of Done)
- `loops/rag.loop.yaml`의 verify.gates(retrieval@k/faithfulness/answer_relevancy)를 전부 통과하는
  RAG 파이프라인이 `ai/`에 존재한다.
- `eval/rag-eval-set.jsonl`이 SRM 더미 문항이 아니라 FR-017 corpus(PRD+FRD) 기반 실제 문항으로
  교체돼 있다.
- FAQ 미매칭/근거 없음 폴백(OQ-010)이 구현돼 있거나, Human PM 확인 전까지 임시 동작(예: "근거 없음"
  고정 응답)으로 명시적으로 대체돼 있고 그 사실이 harness-log/traceability에 기록돼 있다.
- 최소 1회, verifier가 FAIL 판정 → back_to_action → 재시도 → PASS까지의 사이클이 harness-log에
  기록된다(a→b→c 사이클 실증).

## 포함 Task
- T-001: FAQ RAG 파이프라인 구현 + corpus 구축 — ai / in_progress

## Open Issues
- OQ-006(FAQ 근거 corpus 출처)은 PRD+FRD로 잠정 해소했으나, Na-Vendor가 참조했던 "도메인 리서치
  리포트"는 agent-harness에 없다 — corpus를 PRD+FRD로 한정할지, 별도 도메인 문서를 추가할지는
  T-001 진행 중 필요시 ADR-proposed로 확인한다.
- OQ-010(FAQ 미매칭 시 폴백 동작)은 FRD가 명시적으로 미정으로 남긴 항목이다. **지어내지 않는다** —
  `docs/decisions/ADR-007-faq-fallback-when-no-evidence.md`(proposed)로 발의해 Human PM 확인을
  기다리는 중이며, 확인 전까지는 그 ADR의 임시 동작(FR-021/022와 동일 패턴)을 따른다. 확인 전까지
  이 Sprint는 폴백을 최종 확정으로 표시하지 않는다.
- FR-014(합성 샘플 데이터)는 Na-Vendor에서도 미해결 gap이었다 — 이 Sprint 범위 밖이지만, FAQ
  corpus와 별개로 공급업체 샘플 데이터가 필요해지면 별도 Sprint로 분리한다.
