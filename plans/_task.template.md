# Task-XXX: {Task 제목}

- Sprint: sprint-XX
- 도메인: backend | frontend | ai
- 실행 loop: loops/{domain}.loop.yaml
- 상태: todo | in_progress | in_verify | done | back_to_action
- worker: {backend|frontend|rag}-worker (permissions.policy.md 범위 내)

## 목적
왜 이 Task가 필요한가 (어떤 Sprint 목표에 기여하는가).

## 범위 (Scope)
- 건드리는 경로: (도메인 권한 범위 내)
- 건드리지 않는 것:

## 기준 문서 (반드시 확인)
- 프로젝트 헌법: `AGENTS.md`
- (backend면 `openapi.yaml`, frontend면 `design-tokens.json`, ai면 `eval/`)

## Definition of Done (verify 통과 조건)
- loops/{domain}.loop.yaml 의 verify.gates 전부 통과
- (Task 고유 종료 조건)

## 산출물 (record)
- PR, 변경 문서, 스크린샷/eval 리포트 등
- traceability: `docs/traceability.md`에 요구사항→Task→코드→테스트 연결 추가

## 변경 발생 시
- 기준 문서(헌법) 변경이 필요하면 임의 수정 금지 → `docs/decisions/`에 ADR 발의 먼저.
