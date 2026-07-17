---
paths:
  - "backend/**"
  - "frontend/**"
  - "ai/**"
  - "plans/**"
  - "loops/*.loop.yaml"
---

# harness/permissions.policy.md — 도메인별 권한 정책 (단일 원본)

hook(`.claude/hooks/`)이 이 정책을 읽어 PreToolUse 단계에서 강제한다. 정책 밖 접근은 차단하고 `docs/agent-control-log.md`에 기록한다.

## 경로 권한

| Agent | 쓰기 허용 | 읽기 허용 | 차단 |
|-------|-----------|-----------|------|
| orchestrator | `plans/`, `docs/agent-control-log.md` | 전체 | 코드 직접 수정(`backend/`,`frontend/`,`ai/`) |
| backend-worker | `backend/`, `openapi.yaml` | `backend/`, `plans/`, `loops/`, `docs/` | `frontend/`, `ai/`, `eval/`, `plans/` 쓰기 |
| frontend-worker | `frontend/` | `frontend/`, `openapi.yaml`, `plans/`, `docs/` | `backend/`, `ai/`, `eval/`, `plans/` 쓰기 |
| ai-worker | `ai/`, `ai/prompts/` | `ai/`, `eval/`, `plans/`, `docs/` | `backend/`, `frontend/`, `plans/` 쓰기 |
| verifier | `docs/harness-log.md`, `docs/traceability.md` | 전체 | 코드 수정 |

주: orchestrator는 코드는 못 만지지만 계획 문서(`plans/`)와 통제 로그는 쓴다(일감 관리가 본업).
worker는 `plans/`를 읽어 Task를 이해하되 쓰지 않는다(계획 변경은 orchestrator 권한).

## 명령 권한

- worker: 도메인 테스트/빌드/린트 명령만 허용. `git push`·릴리스·배포 명령 차단.
- verifier: 읽기 전용 검증 명령 + eval 실행만 허용.
- 파괴적 명령(`rm -rf`, 강제 push, 시크릿 접근)은 전 Agent 차단.

## 위반 처리

1. hook이 차단 → 2. `agent-control-log.md`에 (agent, 시도, 정책) 기록 → 3. orchestrator에 재위임 신호.
