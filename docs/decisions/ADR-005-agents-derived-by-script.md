# ADR-005: .claude/agents는 agent-specs에서 스크립트로 파생한다

- 상태: accepted
- 날짜: 2026-07-17
- 도메인: harness
- 관련 루프/문서: agent-specs/*.spec.md, scripts/generate_agents.py, .claude/agents/*

## 맥락
Claude Code가 읽는 subagent 정의(`.claude/agents/*.md`)는 특정 frontmatter(name/description/tools)
형식을 요구한다. 이를 손으로 직접 관리하면 "편집 단일 원본은 한 곳"이라는 원칙이 깨지고,
정책(권한)과 agent 정의가 따로 놀 위험이 있다.

## 대안
- (A) `.claude/agents/*.md`를 직접 손편집 — 단일 원본 원칙 붕괴, 정책과 드리프트 위험.
- (B) `agent-specs/*.spec.md`를 단일 원본으로 두고 스크립트로 `.claude/agents/`를 파생.

## 결정
(B). `scripts/generate_agents.py`가 spec의 frontmatter+본문을 읽어 Claude Code 형식으로 변환.
`--check` 플래그로 산출물이 최신인지 CI에서 검사(쓰기 없음). tools 매핑은 스크립트에 두고
경로 단위 강제는 hook(ADR-002)이 담당하도록 역할 분리.

## 근거
- "단일 원본 → 파생" 원칙(AGENTS.md)을 agent 정의에도 일관 적용.
- 생성물에 AUTO-GENERATED 헤더 + 원본 경로를 박아 손편집을 억제.
- `--check`로 spec과 산출물의 불일치를 자동 감지 가능.

## 시행착오 / 검증
- 5개 spec → 5개 agent 생성 후, `--check` 재실행으로 멱등성(재생성해도 변화 없음) 확인.
- verifier.spec에 doc-verify 게이트를 추가한 뒤 재생성 → 반영 확인, `--check` 최신 확인.

## 결과 / 영향
- 생성: `scripts/generate_agents.py`, `.claude/agents/{orchestrator,backend-worker,frontend-worker,rag-worker,verifier}.md`.
- 영향: agent 정의 변경은 항상 spec 편집 → 재생성. `.claude/agents`는 손대지 않음.
- 되돌리기 비용: 낮음. 스크립트 없이도 생성물은 유효하나, 이후 단일 원본 규율이 약해짐.
