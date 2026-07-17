# backend/

`backend-worker` 전용 작업 공간 (`harness/permissions.policy.md`: 쓰기 허용).

- 계약 기준: [`../openapi.yaml`](../openapi.yaml) — 구현은 이 스키마와 일치해야 한다 (contract test).
- 실행 루프: [`../loops/backend.loop.yaml`](../loops/backend.loop.yaml)
- verify: unit+integration test, contract test, lint+typecheck, CI green — `verifier`가 판정.

아직 코드가 없는 스켈레톤 상태.
