# frontend/

`frontend-worker` 전용 작업 공간 (`harness/permissions.policy.md`: 쓰기 허용).

- 스타일 기준: [`../design-tokens.json`](../design-tokens.json)
- API 연동 기준: [`../openapi.yaml`](../openapi.yaml) (읽기 전용 — 계약 변경은 backend 소관)
- 실행 루프: [`../loops/frontend.loop.yaml`](../loops/frontend.loop.yaml)
- verify: typecheck+component test, build, a11y lint — `verifier`가 판정.

아직 코드가 없는 스켈레톤 상태.
