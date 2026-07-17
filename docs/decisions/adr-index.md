# ADR 목록 (adr-index)

되돌리기 어려운 결정의 기록. 새 ADR은 `ADR-000-template.md`를 복제해 작성하고 이 표에 추가한다.

| ADR | 제목 | 상태 | 날짜 | 도메인 |
|-----|------|------|------|--------|
| [001](ADR-001-two-layer-structure.md) | 환경/실행 2계층으로 하네스를 분리한다 | accepted | 2026-07-17 | harness |
| [002](ADR-002-enforce-permissions-via-hook.md) | 권한은 문서가 아니라 PreToolUse hook으로 강제한다 | accepted | 2026-07-17 | harness |
| [003](ADR-003-policy-as-scoped-rules.md) | 정책 문서를 .claude/rules 심볼릭 링크 + paths 스코프로 로드한다 | accepted | 2026-07-17 | harness |
| [004](ADR-004-absorb-concepts-not-restructure.md) | 이사님 번호폴더 구조를 전면 도입하지 않고 개념만 흡수한다 | accepted | 2026-07-17 | harness |
| [005](ADR-005-agents-derived-by-script.md) | .claude/agents는 agent-specs에서 스크립트로 파생한다 | accepted | 2026-07-17 | harness |
| [006](ADR-006-import-navendor-prd-frd-and-real-api.md) | Na-Vendor PRD/FRD를 요구사항으로 재활용하고 FR-016·017·018·020 실제 OpenAI API 사용을 계승한다 | accepted | 2026-07-17 | harness |
| [007](ADR-007-faq-fallback-when-no-evidence.md) | FAQ(FR-017)가 근거를 못 찾았을 때의 폴백 동작(OQ-010) | accepted | 2026-07-17 | ai |

<!-- 상태: proposed | accepted | rejected | superseded -->
