# project-state.md — 현재 상태 스냅샷 (memory/state)

"지금 어디까지 왔나"를 사람이 한눈에 보는 문서. 새 세션·회의·인수인계의 진입점.
루프 record 단계에서 최신화한다 (harness-log가 이력이라면, 이 문서는 현재 단면).

## 기준선
- 프로젝트: 하네스+루프 워크플로우 스캐폴드 (`agent-harness`)
- 핵심 가치: **무인화 · 드리프트 방지 · 재사용성** (2차 미팅 확정)
- 헌법: `AGENTS.md` / 기한: 2026-08-13
- 요구사항: `Na-Vendor` 프로젝트(별도 저장소, 잠정 중단)의 PRD/FRD를 `requirements/`로 재활용
  (`docs/decisions/ADR-006-*.md`). REQ-001~022 / FR-001~023, Na-Vendor 실제 구현(코드)은 가져오지
  않고 이 저장소에서 처음부터 다시 만든다.
- FR-016·017·018·020(자연어 조회/FAQ/평가이력 요약)은 mock이 아니라 **실제 OpenAI API**를 사용하기로
  Na-Vendor ADR-009를 계승(ADR-006). FR-019는 규칙 기반(키워드 사전) 유지.

## 환경 계층 (하네스) — 완료 상태
- [x] 헌법 `AGENTS.md` + 파생 `CLAUDE.md`(200줄 이하, `.claude/rules/` 경로 스코프)
- [x] 권한 정책 `harness/permissions.policy.md` + PreToolUse hook 강제
- [x] worktree 격리 정책, connector 정의
- [x] 검증 기준 단일 원본 `harness/verification.policy.md` (코드 + 문서 산출물)
- [x] eval 하네스 `eval/` + FR-017 실제 RAG 파이프라인 연결
- [x] agent-specs → `.claude/agents/` 생성 스크립트
- [x] Claude Code·Codex 공용 `harness_runtime/` (계약·상태·권한·provider·기록·Draft PR)
- [x] 공용 worker/verifier launch brief `prompts/` + 구조화 출력 schema `harness/schemas/`

## 실행 계층 (계획·루프)
- [x] `loops/{backend,frontend,ai}.loop.yaml` + `_loop.schema.yaml`
- [x] Sprint/Task 계획 `plans/` (Sprint-01·T-001 완료, frontmatter 실행 계약)
- [x] 요구사항 임포트 `requirements/prd.md`, `requirements/frd.md` (Na-Vendor 재활용, ADR-006)
- [x] `FAIL→back_to_action→PASS→record` fake provider 자동 회귀 + Claude↔Codex 양방향 dry-run

## 기록(memory/state)
- [x] `docs/harness-log.md`(이력), `docs/agent-control-log.md`(통제 이벤트)
- [x] `docs/traceability.md`(추적성), `docs/project-state.md`(현재 문서)
- [x] `docs/decisions/` ADR 템플릿과 실제 결정 기록
- [x] 런타임 정제 증거 구조 `docs/runs/{run-id}/` + 로컬 원시 기록 `.harness/runs/`

## 평가 산출물 (과제 PDF §6) — 3종 착수
- [x] ① Agent 통제 기록 `docs/evaluation/agent-control-journal.md`
- [x] ② 하네스 엔지니어링 기록 `docs/evaluation/harness-engineering-log.md`
- [x] ③ 의사결정 문서 `docs/decisions/ADR-001~005` + `adr-index.md`
- [x] 평가기준↔산출물 매핑 `docs/evaluation/evaluation-map.md`(발표용)

## target 기준 파일
- [x] `openapi.yaml`(스켈레톤), `design-tokens.json`(스켈레톤)
- [x] 도메인 폴더 `backend/ frontend/ ai/ ai/prompts/` (README 스켈레톤)

## 남은 큰 일 (HANDOFF "다음 작업" + 2차 미팅)
- [x] `eval/run-eval.py`와 실제 RAG 파이프라인 연결, 도메인 eval-set 교체, T-001 완료
- [x] 선언형 loop를 실행하는 provider-neutral 런타임과 66개 자동 테스트
- [ ] 새 `todo` Task에서 실제 Claude/Codex 교차 provider 유료 smoke run 1회
- [x] `rag-worker` → `ai-worker` 일반화 + `/intake` 부트스트랩 커맨드 신설
  (`docs/superpowers/specs/2026-07-17-generic-harness-intake-design.md`)
- [ ] FRD OQ-007~010(자연어 매핑·요약 규칙·등급조정 키워드·FAQ 폴백) — ADR-proposed 발의 후 Human PM 확인 대기
- [ ] `/intake` 게이트 멱등성 확장 (기존 ADR accepted/harness-log 항목 인식 — 향후 개선 후보, 현재 블로커 아님)
- [ ] UI·API·DB 최소 연결 데모
- [ ] 발표 자료 (무인화·드리프트 방지·재사용성 중심)

<!-- 갱신 규칙: 체크박스와 "남은 큰 일"만 최신 단면으로 유지. 상세 이력은 harness-log.md. -->
