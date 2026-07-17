# Sprint-01: FAQ/RAG(FR-017) 1회전 실증

- 상태: done (2026-07-17, T-001 verify PASS)
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
- [x] `loops/ai.loop.yaml`의 verify.gates(retrieval@k/faithfulness/answer_relevancy)를 전부
  통과하는 RAG 파이프라인이 `ai/`에 존재한다. — verifier 공식 판정 PASS(2026-07-17): retrieval@k
  0.8889, faithfulness 1.0000, answer_relevancy 1.0000 (`docs/harness-log.md` T-001 verify 항목).
- [x] `eval/rag-eval-set.jsonl`이 SRM 더미 문항이 아니라 FR-017 corpus(PRD+FRD) 기반 실제 문항으로
  교체돼 있다. — 9문항, `ai/corpus/chunks.json` 실제 청크 근거.
- [x] FAQ 미매칭/근거 없음 폴백(OQ-010)이 구현돼 있다. `docs/decisions/ADR-007-*.md`가 T-001 착수
  직전 Human PM 채팅 승인으로 `proposed` → `accepted` 전환됨 — 더 이상 임시 동작이 아니다.
- [x] (근사 충족, 아래 "정직한 기록" 참고) 실패→재작업→통과 사이클이 harness-log에 기록된다 —
  다만 정확히 "verifier가 FAIL 판정"한 것은 아니고, code-quality reviewer가 answer_relevancy
  스코어러 설계 결함을 잡아 재작업을 요청한 뒤 verifier가 최초 판정에서 바로 PASS했다. 아래 참고.

### 정직한 기록: DoD 4번 항목의 실제 경위
계획했던 "verifier FAIL → back_to_action → 재시도 → PASS" 사이클은 문자 그대로는 일어나지 않았다.
실제로는: ai-worker의 자체 디버그 실행에서 answer_relevancy 0.798(기준 0.80 미달)이 나왔고, 이건
code-quality reviewer가 "임베딩 코사인 유사도는 정답 문장과의 유사도이지 질문 관련성이 아니다"라는
설계 결함으로 지적해 재작업(LLM judge 방식으로 스코어러 재설계)을 요청했다. 재작업 후 verifier의
공식 판정은 최초 1회 실행에서 바로 PASS했다 — 즉 "실패를 잡아 되돌리고 재시도해 통과시키는" 사이클
자체는 실제로 일어났지만, 그 실패를 잡은 게이트가 계획에서 가정한 verifier eval 게이트가 아니라
code-quality review 게이트였다. 두 게이트 모두 이 하네스의 실제 구성 요소이고 work ≠ verify 원칙을
지켰다는 점은 동일하지만, DoD를 쓸 때 가정한 정확한 경로와는 달랐다는 사실을 숨기지 않는다.

## 포함 Task
- T-001: FAQ RAG 파이프라인 구현 + corpus 구축 — ai / done (verify PASS)

## Open Issues (해소됨)
- ~~OQ-006(FAQ 근거 corpus 출처)~~ — corpus를 PRD+FRD로 한정하는 것으로 T-001 구현에서 확정
  (실제 도메인 리서치 리포트 추가 없이 진행, 결과 PASS). 향후 corpus 확장이 필요해지면 별도 ADR.
- ~~OQ-010(FAQ 미매칭 시 폴백 동작)~~ — `docs/decisions/ADR-007-*.md`가 T-001 착수 직전 accepted로
  전환되어 해소됨.
- FR-014(합성 샘플 데이터)는 Na-Vendor에서도 미해결 gap이었다 — 이 Sprint 범위 밖이며, FAQ corpus와
  별개로 공급업체 샘플 데이터가 필요해지면 별도 Sprint로 분리한다. (이월)
