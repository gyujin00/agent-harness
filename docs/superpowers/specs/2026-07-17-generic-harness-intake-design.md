# 설계: 범용 하네스 템플릿 + `/intake` 부트스트랩 자동화

- 날짜: 2026-07-17
- 상태: 승인됨 (브레인스토밍 대화에서 사용자 승인, 구현 전)
- 관련 문서: `AGENTS.md`, `HANDOFF.md`, `harness/*.md`, `agent-specs/*.spec.md`, `loops/*.loop.yaml`,
  `requirements/README.md`, `docs/decisions/ADR-006-*.md`

## 배경 / 문제

이번 세션에서 `Na-Vendor`의 PRD/FRD를 `agent-harness`에 재활용하는 과정에서, 매번 사람이 직접
"이 저장소가 뭔지", "요구사항을 어디 둘지", "실제 API를 쓸지" 등을 설명하고 확인해줘야 했다.
`agent-harness`는 원래 "도메인 중립 이름이라 SRM 외 과제로도 복제해 재사용할 수 있다"(HANDOFF.md)는
목표를 갖고 있었지만, 실제로는:

1. 도메인 실행 계층(`agent-specs/rag-worker.spec.md`, `loops/rag.loop.yaml`, `eval/`)이 "RAG"라는
   특정 AI 기법 이름과 검증 지표(retrieval@k·faithfulness)에 고정돼 있어 다른 성격의 AI 기능에는
   그대로 안 맞는다.
2. "요구사항 문서를 넣으면 하네스가 스스로 Sprint/Task/ADR을 만들어 시작한다"는 절차가 코드/커맨드로
   존재하지 않고, 매번 사람과의 대화로 재현해야 했다.

**목표**: 다른 Claude Code 세션에서, 어떤 프로젝트의 개발 문서(PRD/FRD/스펙 등)든 `requirements/`에
넣고 `/intake` 한 번만 실행하면, 그 프로젝트에 맞게 하네스가 스스로 커스터마이징되고 첫 Sprint까지
자동으로 초안이 만들어지는 재사용 가능한 폴더 구조(템플릿)를 만든다.

## 비목표 (Non-goals)

- 이 세션에서 이미 만든 SRM 전용 산출물(`requirements/prd.md`·`frd.md`, `plans/sprint-01.md`,
  `docs/decisions/ADR-006/007`, `eval/thresholds.yaml`의 SRM 값)은 건드리지 않는다 — "이 템플릿을
  써본 첫 사례"로 그대로 남긴다.
- MCP 테스트 도구 연동, 허가와 분리된 자동검증 Hook은 이번 설계 범위 밖(별도 라운드).
- 도메인 구조 자체(backend/frontend/ai 3분할)를 완전히 동적으로 만들지 않는다 — 3분할은 고정
  천장이고, 프로젝트에 없는 도메인은 생성만 건너뛴다.
- 요구사항 문서의 표 형식·서술 스타일을 100% 정확히 파싱하는 것은 목표가 아니다(정직한 한계 절 참고).

## 아키텍처 개요

```
requirements/*.md (임의 파일명, 임의 프로젝트)
        │  (사람이 넣음)
        ▼
   /intake  (.claude/commands/intake.md)
        │
        ├─ 1. 문서 전체 읽기
        ├─ 2. 요구사항 ID 추출 ([A-Z]+-\d+ 표 행)
        ├─ 3. 도메인 태깅 (backend/frontend/ai, 없으면 스킵)
        ├─ 4. [게이트] 외부 구현 존재 신호? ──yes──▶ AskUserQuestion 후 대기
        ├─ 5. [게이트] 외부 커넥터/비용 신호? ──yes──▶ 제안만 하고 승인 대기
        ├─ 6. "미정/TBD/확인 필요" 스캔 → ADR-0XX-*.md(proposed) 자동 초안 + adr-index.md
        ├─ 7. docs/traceability.md 골격 행 추가
        ├─ 8. 없는 도메인의 loops/{domain}.loop.yaml, agent-specs/{domain}-worker.spec.md 생성
        ├─ 9. plans/sprint-01.md + Task 1개 초안(상태: planned) — 가장 작은 완결 조각 선정
        ├─ 10. docs/harness-log.md에 실행 기록
        └─ 11. 사람에게 요약 보고
```

`/intake`는 `agent-specs/orchestrator.spec.md`의 상시 watch/위임 역할과는 별개의, **최초 1회성
부트스트랩 절차**다. intake가 만든 `plans/sprint-01.md` 이후의 Sprint/Task 운영은 그대로
`AGENTS.md` §3.5(orchestrator가 점진적으로 관리)를 따른다.

## 컴포넌트

### A. 도메인 스캐폴드 범용화 (기존 파일 리네임/일반화)

| 기존 | 변경 후 | 이유 |
|------|---------|------|
| `agent-specs/rag-worker.spec.md` | `agent-specs/ai-worker.spec.md` | "RAG"는 AI 기능의 한 방식일 뿐, 이름에 특정 기법을 박지 않는다 |
| `loops/rag.loop.yaml` | `loops/ai.loop.yaml` | 위와 동일. verify.gates를 "예시(RAG인 경우 retrieval@k/faithfulness/answer_relevancy)"로 주석 처리, 실제 값은 `/intake`가 문서 성격을 보고 채움 |
| `harness/permissions.policy.md`, `harness/connectors.md`, `.claude/hooks/enforce_permissions.py`의 POLICY 미러 | `rag-worker` → `ai-worker` 참조 전부 치환 | 단일 원본 일관성 |
| `.claude/agents/rag-worker.md` | `.claude/agents/ai-worker.md` | `scripts/generate_agents.py` 재실행으로 파생 |
| `AGENTS.md` 도메인 표 | `rag-worker` → `ai-worker` | 헌법 갱신 |

backend/frontend 쪽(`backend-worker`, `openapi.yaml` 계약 등)은 이미 도메인 중립적이라 이름 변경
없이 유지한다.

### B. `.claude/commands/intake.md` (신규 슬래시 커맨드)

프롬프트 본문에 아래를 명시한다 (실행 주체는 나 자신 — 별도 스크립트가 아니라 지시문 기반 절차):

1. **문서 읽기**: `requirements/` 하위 전체 파일을 이름 가정 없이 Read.
2. **요구사항 추출**: 마크다운 표에서 첫 컬럼이 `[A-Z]+-\d+` 패턴인 행을 요구사항으로 수집(ID,
   설명, 우선순위, 있으면 상태).
3. **도메인 태깅**: "Interface Expectations"/"구현 대상"류 섹션이 있으면 그 하위 Backend/
   Frontend/AI(또는 동의어) 표기를 우선 신뢰. 없으면 키워드 스캔(백엔드/API/DB, 프론트/화면/UI,
   AI/모델/RAG/추천/예측 등). 판별 안 되면 "도메인: 미정"으로 표시하고 계속 진행(막지 않음).
4. **외부 구현 존재 게이트**: 문서 텍스트에서 절대경로, PR 번호, "구현 완료"/"이미 구현된"류 문구,
   run-log 참조를 스캔. 발견 시 그 근거를 인용해 `AskUserQuestion`으로 "이 프로젝트가 이미 다른
   곳에 구현돼 있는지, 이 저장소와의 관계가 무엇인지" 확인 후에만 다음 단계로 진행(이번 세션의
   Na-Vendor 발견을 일반화한 안전장치).
5. **커넥터/비용 게이트**: 외부 API/SaaS 이름(OpenAI, AWS 등 실제 서비스명) 언급을 스캔. 발견 시
   `harness/connectors.md` 추가안을 텍스트로 제시하고 승인 전까지 파일에 쓰지 않는다. 승인되면
   ADR(예: 이번 세션의 ADR-006 패턴)로 기록.
6. **미정 스캔 → ADR-proposed 자동 초안**: "미정/TBD/확인 필요/OQ-"류 패턴을 스캔해 항목마다
   `docs/decisions/ADR-0XX-*.md`를 `ADR-000-template.md` 기준으로 `상태: proposed`로 생성,
   출처(문서/섹션)를 "맥락" 절에 인용. `adr-index.md`에 행 추가.
7. **traceability 골격**: `docs/traceability.md`에 추출된 요구사항 ID별 행 추가(코드/테스트 칸은
   `-`). 이미 있는 ID는 건너뜀(멱등성).
8. **도메인 스캐폴드 생성**: 3단계에서 태깅된 도메인 중 `loops/{domain}.loop.yaml` 또는
   `agent-specs/{domain}-worker.spec.md`가 없는 경우에만 범용 템플릿(A절 결과물)을 복제해 생성.
   이미 있으면 스킵.
9. **Sprint-01 후보 작성**: 우선순위 "필수/must" 항목 중 가장 작고 하나로 완결되는 조각(도메인당
   1개, 여러 기능을 한 번에 넣지 않음 — 이번 세션 "FR-017 하나부터" 판단의 일반화)을 골라
   `plans/sprint-01.md` + Task 1개를 상태 `planned`로 생성. `plans/sprint-index.md`,
   `plans/task-index.md` 갱신.
10. **기록**: `docs/harness-log.md`에 이번 intake 실행을 한 항목으로 남긴다(무엇을 스캔했고, 몇 개
    요구사항/ADR-proposed/도메인을 만들었는지).
11. **요약 보고**: 사람에게 도메인별 요구사항 수, 생성된 ADR-proposed 목록, Sprint-01 제안 내용,
    대기 중인 게이트(4/5번에서 확인 대기 중인 것)를 보고.

### C. 멱등성 규칙

- 요구사항 ID가 이미 `docs/traceability.md`에 있으면 재추출하지 않는다.
- 같은 "미정" 문구(문서 내 위치+텍스트 해시로 판별)에 대한 ADR-proposed가 이미 있으면 중복 생성하지
  않는다.
- 도메인 loop/spec 파일이 이미 있으면 덮어쓰지 않는다(사람이 그 사이 손으로 고쳤을 수 있음).

## 데이터 흐름 요약

`requirements/*` → (읽기 전용, 파싱만) → `docs/traceability.md`(신규 행) +
`docs/decisions/ADR-0XX-*.md`(proposed) + `loops/*.yaml`·`agent-specs/*.spec.md`(없는 도메인만) +
`plans/sprint-01.md`+`plans/task-00N.md`(planned) + `docs/harness-log.md`(실행 기록) → 사람에게
채팅으로 요약.

## 에러 처리 / 예외

- `requirements/`가 비어있으면 intake는 "처리할 문서가 없다"고 보고하고 아무것도 쓰지 않는다.
- 요구사항 ID 패턴이 전혀 매칭되지 않으면(문서 스타일이 표 기반이 아닐 때), 전체를 하나의 미분류
  블록으로 보고하고 사람에게 "이 문서에서 어떻게 요구사항을 뽑아낼지" 확인을 요청한다 — 잘못된
  ID를 지어내지 않는다.
- 4/5번 게이트에서 사람 응답을 기다리는 동안 6~11번은 진행하지 않는다(게이트는 순서대로, 뒷단계가
  앞단계의 확인 없이 앞서 나가지 않게).

## 테스트/검증 계획

구현 후 다음으로 "진짜 범용인가"를 확인한다:

1. **회귀 확인**: `requirements/`에 이미 있는 SRM PRD/FRD로 `/intake`를 재실행 → 기존
   `docs/traceability.md`/ADR-006/007/sprint-01과 충돌·중복 생성이 없어야 한다(멱등성 검증).
2. **이종 프로젝트 드라이런**: SRM과 무관한 가상의 미니 PRD(예: "AI 없이 backend+frontend만 있는
   TODO 앱" 1페이지)를 임시 디렉터리에 만들어 `/intake` 로직을 수행 — `ai/` 관련 파일이 전혀
   생성되지 않는지, 도메인 태깅이 backend/frontend만 잡히는지 확인.
3. **게이트 유발 드라이런**: "이미 `workspaces/foo/`에 구현됨"류 문구가 있는 가상 문서로
   `/intake`를 돌려 4번 게이트가 실제로 멈추고 확인을 요청하는지 확인.
4. 위 시나리오 결과는 `docs/harness-log.md`에 검증 이력으로 남긴다(이 프로젝트의 기존 관례:
   ADR/hook 변경 후 항상 수동 시나리오로 검증하고 결과를 기록).

## 정직한 한계

- 텍스트 패턴 기반 파싱이므로 표 형식이 아니거나 ID 컨벤션이 특이한 문서는 요구사항을 놓칠 수
  있다. 안전망은 `docs/traceability.md`의 기존 "커버리지 점검 질문"(기준 문서에 있는데 Task가
  없는 것은?)이 사람이 나중에 잡아내는 역할을 한다.
- 도메인 태깅과 "가장 작은 완결 조각" 선정은 휴리스틱이라 항상 옳지 않을 수 있다 — 그래서 Sprint는
  `planned` 상태로만 만들고 `active`로 스스로 승격하지 않는다(사람이 검토 후 착수).
- 이 설계는 backend/frontend/ai라는 소프트웨어 제품 개발 프로젝트를 전제한다. 완전히 다른 성격의
  프로젝트(예: 순수 데이터 분석 보고서)에는 이 3분할 자체가 안 맞을 수 있다 — 그 경우는 범위 밖.
