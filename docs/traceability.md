# traceability.md — 추적성 매트릭스 (memory/state)

요구사항이 문서·Task·코드·테스트까지 어떻게 이어지는지 한눈에 보는 단일 기록.
"추적성(요구사항 → 문서 → Task → 코드 → 테스트)"을 증명하는 산출물 (2차 미팅 성공 기준).

worker/verifier가 Task 완료(record) 시 자기 행을 갱신한다.

## 매트릭스

| 요구사항 ID | 기준 문서 | Task | 도메인 | 코드/PR | 테스트·검증 | 상태 |
|-------------|-----------|------|--------|---------|-------------|------|
| FR-017 (REQ-017) | `requirements/frd.md`, `plans/sprint-01.md` | T-001 | ai | PR #— | eval 리포트(미실행) | todo |

<!-- FR-017의 기준 문서 우선순위: requirements/frd.md(§3 FR-017, §5 BR-007/BR-009, §11 OQ-006/OQ-010)
     > requirements/prd.md(REQ-017) > docs/decisions/ADR-006(실 API 계승 근거). -->

<!--
규칙:
- 한 요구사항이 여러 Task로 갈라지면 행을 나눠 쓴다.
- 코드/PR·테스트 칸은 record 단계에서 채운다 (verify 통과 후).
- ADR로 기준이 바뀌면 영향받은 행의 '기준 문서' 칸을 갱신하고 harness-log에 남긴다.
-->

## 커버리지 점검 질문 (verifier가 최종 통합에서 확인)
- 기준 문서에 있는 요구사항 중 Task가 없는 것은? (누락)
- Task는 있는데 요구사항 근거가 없는 것은? (범위 밖 작업)
- 코드는 있는데 테스트/검증이 없는 것은? (미검증)
