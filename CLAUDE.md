# CLAUDE.md (파생 — 직접 편집 금지)

<!-- 생성 규칙: AGENTS.md를 임포트. harness/permissions.policy.md, harness/worktree.md,
     harness/verification.policy.md는 .claude/rules/ 심볼릭 링크 + paths frontmatter로
     backend/frontend/ai/plans/loops 작업 시에만 자동 로드된다 (여기서 다시 @import하지 않음).
     harness/connectors.md는 paths 스코프가 없어 항상 로드된다. 200줄 이하 유지. -->

@import ./AGENTS.md

## 빠른 참조

- 환경(하네스)은 `harness/`, `.claude/`, `eval/`, `docs/`가 담당한다.
- 실행(계획·루프)은 `plans/`(Sprint·Task)와 `loops/*.loop.yaml`이 담당한다.
- 사람 → orchestrator(목표를 Sprint→Task로 분해) → worker → verifier → record.
- work ≠ verify. 검증 기준은 `harness/verification.policy.md`(코드+문서 산출물)를 따른다.
- 기록: `docs/harness-log.md`(이력), `docs/traceability.md`(추적성), `docs/project-state.md`(현재 단면).
- 도메인 정책(`permissions.policy.md`, `worktree.md`, `verification.policy.md`)은 `.claude/rules/`를 통해
  backend/frontend/ai/plans/loops 작업 시에만 자동 로드된다. `connectors.md`는 항상 로드된다.
