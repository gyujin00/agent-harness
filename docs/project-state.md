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
- [x] eval 하네스 골격 `eval/` (run_pipeline 연결은 미완 — 실제 ai/ 파이프라인 대기)
- [x] agent-specs → `.claude/agents/` 생성 스크립트

## 실행 계층 (계획·루프)
- [x] `loops/{backend,frontend,rag}.loop.yaml` + `_loop.schema.yaml`
- [x] Sprint/Task 계획 `plans/` (인덱스 + 템플릿) — 실제 Sprint/Task는 아직 없음
- [x] 요구사항 임포트 `requirements/prd.md`, `requirements/frd.md` (Na-Vendor 재활용, ADR-006)
- [ ] 첫 Sprint 정의 및 Task 점진 생성 — 후보: FR-017(FAQ/RAG), AI 워크스트림 a→b→c 사이클 실증

## 기록(memory/state)
- [x] `docs/harness-log.md`(이력), `docs/agent-control-log.md`(통제 이벤트)
- [x] `docs/traceability.md`(추적성), `docs/project-state.md`(현재 문서)
- [x] `docs/decisions/` ADR 템플릿(대안·시행착오 필드 보강) — **Accepted ADR 5건**(ADR-001~005)

## 평가 산출물 (과제 PDF §6) — 3종 착수
- [x] ① Agent 통제 기록 `docs/agent-control-journal.md`(회차 5건 서술)
- [x] ② 하네스 엔지니어링 기록 `docs/harness-engineering-log.md`(설계 근거·시행착오 4건)
- [x] ③ 의사결정 문서 `docs/decisions/ADR-001~005` + `adr-index.md`
- [x] 평가기준↔산출물 매핑 `docs/evaluation-map.md`(발표용)

## target 기준 파일
- [x] `openapi.yaml`(스켈레톤), `design-tokens.json`(스켈레톤)
- [x] 도메인 폴더 `backend/ frontend/ ai/ ai/prompts/` (README 스켈레톤)

## 남은 큰 일 (HANDOFF "다음 작업" + 2차 미팅)
- [ ] `eval/run-eval.py` 파이프라인/스코어러 실제 연결 (실제 ai/ 구현 시, 실제 OpenAI API 호출)
- [ ] `eval/rag-eval-set.jsonl` 실제 도메인 문항 교체 (`requirements/frd.md` FR-017/BR-007/BR-009 기준)
- [ ] 첫 Sprint→Task→loop→verify→record 1회전 실증 (FR-017 후보)
- [ ] FRD OQ-007~010(자연어 매핑·요약 규칙·등급조정 키워드·FAQ 폴백) — ADR-proposed 발의 후 Human PM 확인 대기
- [ ] `/intake` 게이트 멱등성 확장 (기존 ADR accepted/harness-log 항목 인식 — 향후 개선 후보, 현재 블로커 아님)
- [ ] UI·API·DB 최소 연결 데모
- [ ] 발표 자료 (무인화·드리프트 방지·재사용성 중심)

<!-- 갱신 규칙: 체크박스와 "남은 큰 일"만 최신 단면으로 유지. 상세 이력은 harness-log.md. -->
