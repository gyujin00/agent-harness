# harness/connectors.md — 외부 연결 (단일 원본)

Agent가 접근 가능한 외부 시스템과 그 용도. connector를 늘리는 것은 곧 통제 범위를 늘리는 것이므로 최소로 유지한다.

## 작업 소스 (watch/record 대상)

| connector | 용도 | 사용 루프 단계 |
|-----------|------|----------------|
| GitHub | 이슈·PR·CI 상태·코드 | watch, action, verify, record |
| Linear (선택) | 일감 트래킹 | watch, record |
| Slack (선택) | 실패 신호·알림 | watch(trigger), record |

## AI 도메인 전용 connector

| connector | 용도 | 비고 |
|-----------|------|------|
| Vector DB (Chroma) | RAG 검색 인덱스 | `ai/` 도메인만 접근 |
| Embedding API (OpenAI) | 청크/질의 임베딩 (FR-016~018, FR-020) | 실제 외부 API 호출 (`docs/decisions/ADR-006-*.md`). 모델 변경은 ADR 필수 |
| LLM API (OpenAI, Chat Completions) | FAQ 답변 생성(FR-017)·자연어 질의 해석(FR-016/020)·평가이력 요약(FR-018) | 실제 외부 API 호출 (`docs/decisions/ADR-006-*.md`). `ai/` 도메인만 접근, mock으로 되돌리는 것도 ADR 필수 |

## 원칙

- connector 자격증명은 Agent 컨텍스트에 노출하지 않는다. 실행 환경 변수/시크릿 매니저로 주입한다.
- 도메인별 접근 범위는 `permissions.policy.md`가 강제한다. 예: `frontend-worker`는 Vector DB에 접근하지 않는다.
