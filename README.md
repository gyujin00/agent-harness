# 하네스 + 루프 워크플로우 스캐폴드

백엔드·프론트엔드·AI(RAG/NLP)를 **하나의 하네스(환경)** 위에서 **도메인별 루프(실행)**로 개발하기 위한 뼈대.

## 두 계층
- **환경 · Harness engineering** — 무엇을 주고 어떻게 통제할지. `harness/`, `.claude/`, `eval/`, `docs/`.
- **실행 · Loop engineering** — 무엇을 반복시킬지. `plans/`(Sprint·Task) + `loops/*.loop.yaml` (target→trigger→action→verify→record).

## 단일 원본 → 파생
손으로 편집하는 곳 (Git이 유일한 컨텍스트 원본):
- `AGENTS.md` (헌법) → `CLAUDE.md` 파생 (`@import ./AGENTS.md`만)
- `harness/*` (connector·권한·worktree·검증정책) → `permissions.policy.md`, `worktree.md`, `verification.policy.md`는
  `.claude/rules/*` 심볼릭 링크로 파생, `paths:` frontmatter로 도메인 작업 시에만 로드
- `agent-specs/*.spec.md` → `.claude/agents/` 파생
- `plans/*` (Sprint·Task 계획, orchestrator 관리)
- `loops/*.loop.yaml` (`_loop.schema.yaml` 참조)
- `eval/*` (AI verify 기준)

임포트만 하고 손편집하지 않는 곳:
- `requirements/*` (PRD/FRD — 외부 프로젝트에서 가져온 요구사항 스냅샷, 갱신은 재복사+ADR)

## 평가 산출물 (과제 PDF §6 — 코드 외 핵심)
이 과제는 완성도가 아니라 **과정·통제·근거**를 본다. docs/가 곧 평가 대상이다.
- ① Agent 통제: `docs/agent-control-journal.md`
- ② 하네스 엔지니어링: `docs/harness-engineering-log.md`
- ③ 의사결정·시행착오: `docs/decisions/ADR-*` (`adr-index.md`)
- 평가기준↔산출물 매핑(발표용): `docs/evaluation-map.md`

## 핵심 규칙 3가지
1. **work ≠ verify** — worker가 만든 결과는 별도 `verifier`가 `harness/verification.policy.md` 기준으로 판정.
2. **사람 → orchestrator → worker** — 사람은 worker에게 직접 프롬프트하지 않고, orchestrator가 목표를 Sprint→Task로 분해해 위임.
3. **모든 루프는 record로 끝난다** — `docs/harness-log.md`·`traceability.md`·`project-state.md` + 필요 시 ADR.

## 2차 미팅 피드백 반영 (무인화·드리프트 방지·재사용성)
- **Sprint/Task** (`plans/`): Task를 미리 다 만들지 않고 Sprint 수행하며 점진 생성.
- **문서 검증** (`harness/verification.policy.md`): 코드뿐 아니라 AI 생성 문서(도메인/API/ERD)도 원천 대조.
- **추적성** (`docs/traceability.md`): 요구사항→문서→Task→코드→테스트 연결.
- **현재 상태** (`docs/project-state.md`): 사람이 한눈에 보는 진행 단면.

## AI 도메인이 특별한 이유
백엔드/프론트의 verify는 test pass/fa