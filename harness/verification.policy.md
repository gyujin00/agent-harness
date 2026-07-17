---
paths:
  - "backend/**"
  - "frontend/**"
  - "ai/**"
  - "plans/**"
  - "loops/*.loop.yaml"
---

# harness/verification.policy.md — 산출물별 검증 기준 (단일 원본)

verifier가 참조하는 검증 기준의 단일 원본. "Verifier가 있다"만으로는 부족하고,
**무엇을·어떤 기준으로·언제 통과/실패시키는지**를 명시한다 (2차 미팅 피드백).

핵심 원칙: **코드만 검증하지 않는다.** AI가 소스/DB에서 생성한 문서 산출물도 원천과 대조해 검증한다.

## 산출물별 검증 기준

| 산출물 | 참조 기준 | 검사 항목 | 통과 조건 |
|--------|-----------|-----------|-----------|
| 소스 코드 (backend) | `openapi.yaml`, 도메인 규칙 | unit/integration, contract, lint, CI | 전부 green |
| 소스 코드 (frontend) | `design-tokens.json`, `openapi.yaml` | typecheck, component test, build, a11y | 전부 green |
| RAG 파이프라인 (ai) | `eval/rag-eval-set.jsonl` | retrieval@k, faithfulness, answer_relevancy | `eval/thresholds.yaml` 기준선 이상 |
| 도메인 문서 | 원천 소스·요구사항 | 비즈니스 규칙 일치, 범위 누락 없음 | 불일치 0건 |
| API 명세 (openapi.yaml) | 실제 Controller/DTO/Error | Endpoint·Method·Schema·Required·Status Code | 불일치 0건 |
| 데이터 문서 (ERD 등) | 실제 스키마 | 테이블·컬럼·관계·제약조건 | 불일치 0건 |
| 화면 명세 | 요구 기능 | 화면 구성·화면–API 매핑 | 불일치 0건 |
| 아키텍처 문서 | 실제 배포·모듈 | 컴포넌트·데이터 흐름 일치 | 불일치 0건 |
| Sprint/Task | `plans/`, 헌법 | Scope·우선순위·DoD 일치 | 기준 문서와 충돌 0건 |
| 최종 통합 | 전체 | 문서·코드·화면·DB 간 모순 | 모순 0건 |

## 문서 검증(doc-verify)이 잡아야 하는 AI 오류 유형

소스에 없는 기능 추론, 테이블 관계 오해, API 입출력 누락, 화면–API 매핑 오류,
도메인 정책 왜곡, 기술 버전 오인, Scope 누락, 문서 간 상충.

## verify 게이트 명세 규약 (모든 게이트 공통)

각 게이트는 다음을 명시한다.

- 검증 대상 (무엇을)
- 참조하는 기준 문서 (무엇에 비추어)
- 검사 항목 (어떤 항목을)
- 통과 조건 / 실패 조건
- 실패 시 되돌아가는 단계 (`on_fail`)
- 자동 재작업 허용 횟수
- 사람 승인이 필요한 조건 (예: N회 실패 시 Human Approval)
- 결과 저장 위치 (`docs/harness-log.md`, 필요 시 `docs/traceability.md`)

예시:

```text
API Spec Verifier
- 대상: openapi.yaml
- 기준: 실제 Controller, DTO, Error Policy
- 검사: Endpoint, Method, Schema, Required, Status Code
- 통과: 불일치 0건 / 실패: API 문서 생성 단계로 반환
- 2회 실패: Human Approval 요청
- 결과: docs/harness-log.md
```

## 원칙

- verify는 항상 worker와 분리된 `verifier`가 수행한다 (work ≠ verify).
- 문서 검증 실패도 코드 실패와 동일하게 `on_fail` 정책을 따른다 (기본 `back_to_action`).
