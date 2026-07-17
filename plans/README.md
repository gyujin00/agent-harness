# plans/ — Sprint·Task 계획 (실행 계층)

목표(human.goal)나 Ops 스캔에서 나온 일감을 **orchestrator가 Sprint→Task로 점진 분해**하는 곳.
loops/가 "무엇을 어떻게 반복하는가(게임 규칙)"라면, plans/는 "지금 무엇을 할 것인가(현재 backlog)"다.

## 핵심 원칙 (2차 미팅 피드백 반영)

- **Task를 미리 다 만들지 않는다.** Scope/Phase로 Sprint를 먼저 정의하고, Sprint를 수행하며 Task를 추가한다.
- **Task = loop를 트리거하는 일감 단위.** 각 Task는 도메인(`backend|frontend|ai`)을 갖고,
  해당 `loops/{domain}.loop.yaml`을 통해 worker에 위임된다 (`action`), verifier가 판정한다 (`verify`).
- **Task 생성 시 관련 문서를 함께 갱신한다** (`docs/traceability.md`에 연결 관계 기록).
- **orchestrator만 plans/에 쓴다** (`harness/permissions.policy.md`). worker/verifier는 읽기만.

## 파일

| 파일 | 역할 |
|------|------|
| `sprint-index.md` | 전체 Sprint 목록·상태 |
| `task-index.md` | 전체 Task 목록·도메인·상태·연결 loop |
| `_sprint.template.md` | Sprint 문서 템플릿 (복제해서 `sprint-XX.md` 생성) |
| `_task.template.md` | Task 문서 템플릿 (복제해서 `task-XXX.md` 생성) |

## 상태 전이

```text
Sprint:  planned → active → done
Task:    todo → in_progress → in_verify → done | back_to_action(재시도)
```
