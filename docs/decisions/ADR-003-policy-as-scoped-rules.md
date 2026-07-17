# ADR-003: 정책 문서를 .claude/rules 심볼릭 링크 + paths 스코프로 로드한다

- 상태: accepted
- 날짜: 2026-07-17
- 도메인: harness
- 관련 루프/문서: CLAUDE.md, harness/*.md, .claude/rules/*

## 맥락
CLAUDE.md가 `@import ./harness/permissions.policy.md` 등으로 정책 문서를 전부 임포트하면,
모든 세션 시작 시 항상 로드돼 컨텍스트(토큰)를 낭비하고 중요한 규칙이 묻힌다.
반면 정책은 도메인 작업(backend/frontend/ai)을 할 때만 필요하다.

## 대안
- (A) CLAUDE.md에서 `@import` 유지 — 항상 로드, 토큰 낭비.
- (B) 정책 내용을 CLAUDE.md에 복붙 — 단일 원본 붕괴(이중 관리).
- (C) `harness/*.md`에 `paths:` frontmatter를 달고 `.claude/rules/`에 심볼릭 링크 —
  해당 경로 작업 시에만 자동 로드, 원본은 harness/ 한 곳 유지.

## 결정
(C). `permissions.policy.md`·`worktree.md`·`verification.policy.md`는 paths 스코프(backend/**,
frontend/**, ai/**, plans/**, loops/*.loop.yaml)로 조건부 로드. `connectors.md`는 스코프 없이 항상 로드.
CLAUDE.md는 `@import ./AGENTS.md`만 남긴다.

## 근거
- 공식 memory 문서의 `.claude/rules/` + `paths` frontmatter 메커니즘이 정확히 이 용도.
- 심볼릭 링크라 원본이 harness/ 한 곳뿐 → 단일 원본 원칙 유지, 이중 관리 없음.
- CLAUDE.md를 200줄 → 15줄로 축소해 "지침은 짧게, 상세는 필요할 때만"(2차 미팅) 충족.

## 시행착오 / 검증
- 이 개선은 참고 PDF(클로드_코드_구조) 검토 중, `.claude/rules/`가 우리의 `@import` 방식보다
  idiomatic함을 확인하면서 도출됐다.
- `readlink -f`로 링크 4개가 원본을 정상 해석하는지, `find -xtype l`로 끊어진 링크가 없는지 검증.
- frontmatter YAML 파싱 확인, CLAUDE.md 15줄(<200) 확인.

## 결과 / 영향
- 생성: `.claude/rules/{connectors,permissions-policy,worktree,verification-policy}.md`(심볼릭 링크).
- 변경: `CLAUDE.md`(import 축소), `AGENTS.md §5`, `harness/*.md`(frontmatter 추가).
- 되돌리기 비용: 낮음(링크 삭제 후 CLAUDE.md에 @import 복원).
