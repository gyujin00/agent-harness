# AGENTS.md — 프로젝트 헌법 (단일 원본)

> 이 문서가 유일한 헌법 원본입니다. `CLAUDE.md`는 이 파일을 `@import`한 파생물이며 직접 편집하지 않습니다.
> 편집 가능한 단일 원본: `AGENTS.md`, `harness/*`, `agent-specs/*.spec.md`, `loops/*.loop.yaml`, `eval/*`, `plans/*`.
> 나머지(`CLAUDE.md`, `.claude/agents/`, `.claude/hooks/`)는 생성 스크립트로 파생합니다.
> `requirements/*`(PRD/FRD)는 외부에서 임포트한 요구사항 스냅샷이며 손편집 대상이 아니다 — 갱신은
> 재복사 + ADR로 남긴다 (`requirements/README.md` 참고).

## 0. 두 계층 모델

- **환경 계층 (Harness engineering)** — Agent에게 *무엇을 주고 어떻게 통제할지* 정의하는 정적인 판.
  구성: `harness/`, `.claude/skills`, `.claude/hooks`, worktree, connector, `eval/`, `docs/`(기록).
- **실행 계층 (Loop engineering)** — 그 판 위에서 *무엇을 반복시킬지* 정의하는 동적인 게임.
  구성: `plans/*`(Sprint·Task 계획) + `loops/*.loop.yaml`(target → trigger → action → verify → record).

한 문장 원칙: **환경은 손대는 사람이 바꾸고, 실행은 plan과 loop.spec이 바꾼다.**

## 1. 통제 원칙 (모든 Agent 공통)

1. **work와 verify를 절대 같은 Agent가 겸하지 않는다.** worker가 만든 결과는 별도 `verifier`가 판정한다.
2. **사람은 worker에게 직접 프롬프트하지 않는다.** 일감은 `orchestrator`를 통해 위임된다.
3. **모든 작업은 격리된 worktree에서 수행**한다 (`harness/worktree.md`).
4. **경로/명령 권한은 도메인 정책을 따른다** (`harness/permissions.policy.md`). 정책 밖 접근은 hook이 차단한다.
5. **결정은 ADR로 남긴다.** 임베딩 모델·청크 전략·아키텍처 변경 등 되돌리기 어려운 선택은 `docs/decisions/`.
6. **세션은 기록으로 끝난다.** 모든 루프의 마지막 단계 `record`는 필수이며 생략 불가.

## 2. 도메인 경계

| 도메인 | 코드 경로 | worker | verify 성격 |
|--------|-----------|--------|-------------|
| Backend | `backend/` | `backend-worker` | 결정적 (test/contract/CI) |
| Frontend | `frontend/` | `frontend-worker` | 준결정적 (typecheck/build/a11y) |
| AI | `ai/` | `ai-worker` | 비결정적 → **eval 회귀** (`eval/`) |

세 도메인은 하나의 하네스를 공유하고, `loops/{domain}.loop.yaml`로만 실행이 갈린다.

## 3. 루프 종류

- **Goal loop** — 사람이 목표 지정 → 목표 안에서 반복 → 조건 만족 시 종료. (신규 기능)
- **Ops loop** — orchestrator가 주기적으로 repo/CI 스캔 → 일감 발견 → 위임 → 종료. (유지보수/자동화)

같은 도메인이 두 루프로 모두 돌 수 있으며, `trigger` 필드가 `human.goal`인지 스캔 이벤트인지로 갈린다.

## 3.5 Sprint와 Task (계획 계층)

목표를 곧바로 loop로 던지지 않고, orchestrator가 `plans/`에서 **Sprint→Task로 점진 분해**한다.
Sprint/Task가 인용하는 요구사항 ID(REQ-*/FR-*)의 기준 문서는 `requirements/prd.md`,
`requirements/frd.md`다 (외부 임포트, 손편집 금지 — §0 참고).

- **Task를 미리 다 만들지 않는다.** Scope/Phase로 Sprint를 먼저 정의하고, Sprint를 수행하며 Task를 추가한다.
- **Task = loop를 트리거하는 최소 일감.** 각 Task는 도메인 하나를 갖고 `loops/{domain}.loop.yaml`의
  `action`(worker 위임) → `verify`(verifier 판정) → `record`를 거친다.
- **Task 생성 시 추적 관계를 남긴다.** 요구사항→문서→Task→코드→테스트 연결을 `docs/traceability.md`에 기록한다.
- **plans/는 orchestrator만 쓴다.** worker/verifier는 읽기만 (`harness/permissions.policy.md`).
- 상태 전이: Sprint `planned→active→done`, Task `todo→in_progress→in_verify→done | back_to_action`.

파일: `plans/sprint-index.md`, `plans/task-index.md`, `plans/_sprint.template.md`, `plans/_task.template.md`.

## 4. 기록(memory/state) 규약

### 4.1 실행 기록 (하네스 운영용)
- `docs/harness-log.md` — 세션별 통제 기록(이력). 다음 루프가 읽어 컨텍스트를 잇는다.
- `docs/agent-control-log.md` — Agent 위임/차단/재시도 이벤트(기계 로그).
- `docs/traceability.md` — 추적성 매트릭스(요구사항→문서→Task→코드→테스트). Task record 시 갱신.
- `docs/project-state.md` — 현재 상태 스냅샷(단면). 새 세션·회의·인수인계의 진입점.

### 4.2 평가 산출물 (과제 PDF §6 "코드 외 핵심 산출물")
- `docs/agent-control-journal.md` — ① Agent 활용·통제 기록(목표·맥락·제약·프롬프트·판단·교정, 서사).
- `docs/harness-engineering-log.md` — ② 하네스 설계 근거·시행착오·개선 시도(정책의 '왜').
- `docs/decisions/ADR-XXX-*.md` + `adr-index.md` — ③ 의사결정·시행착오(대안·근거 포함). 되돌리기 어려운 결정.
- `docs/evaluation-map.md` — 평가기준 ↔ 산출물 1:1 매핑(발표용 인덱스).

원칙: 실행 로그(4.1)는 기계·다음 루프가 읽고, 평가 산출물(4.2)은 사람·평가자가 읽는다. 둘 다 record 대상.

## 5. CLAUDE.md 관리

- `CLAUDE.md`는 200줄 이하로 유지한다. `AGENTS.md`만 `@import`한다.
- `harness/permissions.policy.md`, `harness/worktree.md`는 `.claude/rules/`에 심볼릭 링크로 연결하고
  `paths:` frontmatter(`backend/**`, `frontend/**`, `ai/**`, `loops/*.loop.yaml`)를 달아
  해당 경로 작업 시에만 자동 로드되게 한다 (CLAUDE.md에서 다시 `@import`하지 않음 — 중복 로드 방지).
  `harness/connectors.md`는 paths 스코프 없이 항상 로드된다.
- 두 계정(토큰 한도) 사용 시, Git이 유일한 컨텍스트 원본이다. 로컬 상태에 의존하지 않는다.
