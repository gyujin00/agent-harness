---
description: requirements/의 프로젝트 문서를 읽어 하네스를 자동으로 부트스트랩한다 (Sprint-01 초안 + ADR-proposed + 도메인 스캐폴드)
---

# /intake — 요구사항 문서 기반 하네스 부트스트랩

당신은 이 하네스의 **최초 1회성 부트스트랩 절차**를 수행한다. 이 절차는
`agent-specs/orchestrator.spec.md`의 상시 watch/위임 역할과는 별개다 — intake는
`plans/sprint-01.md`까지만 만들고, 그 이후 Sprint/Task 운영은 `AGENTS.md` §3.5(orchestrator가
점진적으로 관리)를 그대로 따른다. 설계 근거:
`docs/superpowers/specs/2026-07-17-generic-harness-intake-design.md`.

## 0. 선행 확인
`requirements/`가 비어 있으면: "처리할 문서가 없습니다. PRD/FRD 등 개발 문서를 requirements/에
넣고 다시 `/intake`를 실행하세요."라고만 보고하고 종료한다. 아무 파일도 쓰지 않는다.

## 1. 문서 읽기
`requirements/` 하위의 모든 파일을 이름을 가정하지 않고 전부 Read한다(`prd.md`/`frd.md`라는
이름을 전제하지 않는다 — 프로젝트마다 파일명이 다를 수 있다).

## 2. 요구사항 추출
각 문서에서 마크다운 표의 첫 컬럼이 `[A-Z]+-\d+` 패턴(REQ-001, FR-017, US-12 등 접두어 무관)인
행을 요구사항으로 수집한다. 각 항목에 대해 ID·설명·우선순위(있으면)·출처 문서를 기록해둔다.

표 형식이 전혀 없는 문서라면(서술형뿐이라면), 요구사항을 지어내지 말고 "이 문서에서 표 형태의
요구사항 목록을 찾지 못했습니다. 어떻게 요구사항 단위를 나눌지 알려주세요"라고 사람에게 확인을
요청한 뒤 그 문서는 3~9단계에서 제외한다(다른 문서는 계속 처리한다).

## 3. 도메인 태깅
2단계에서 모은 요구사항마다 backend/frontend/ai 중 도메인을 태깅한다.
- 우선 신뢰: 문서에 "Interface Expectations", "구현 대상", "화면/API/AI 설계" 같은 절이 있고
  그 아래 Backend/Frontend/AI(또는 백엔드/프론트엔드/AI, UI/서버/모델 등 동의어)로 요구사항 ID를
  나열해뒀으면 그 매핑을 그대로 쓴다.
- 없으면 키워드 스캔: 설명 텍스트에 API·DB·서버·백엔드 → backend / 화면·UI·프론트·컴포넌트 →
  frontend / AI·모델·RAG·추천·예측·분류·LLM → ai.
- 그래도 판별 안 되면 "도메인: 미정"으로 남기고 계속 진행한다(막지 않는다 — 나중에
  `docs/traceability.md` 커버리지 점검에서 사람이 잡아낸다).
- 세 도메인 중 문서 전체에서 단 한 번도 언급되지 않은 도메인은, 8~9단계에서 그 도메인용 파일을
  아예 만들지 않는다(있는 도메인만 스캐폴딩한다).

## 4. [게이트 1] 외부 구현 존재 신호 확인
문서 텍스트 전체에서 다음 신호를 스캔한다: 이 저장소 밖의 절대 경로/디렉터리명 언급, PR 번호
언급("PR #", "pull request"), "구현 완료"/"이미 구현된"/"완료됨" 류 문구, run-log·실행 기록
경로 언급(예: `docs/records/`, `run-log.md` 등).

하나라도 발견되면, 그 근거(문서명·인용 구절)를 그대로 사람에게 보여주며 다음을 확인받을 때까지
**5단계 이후로 진행하지 않는다** (AskUserQuestion 사용):

> "이 문서가 가리키는 프로젝트가 이미 다른 곳에 구현되어 있는 것으로 보입니다 — [인용]. 이
> 저장소와의 관계(재활용/이어받기/무관)를 확인해주시겠어요?"

확인 응답을 받으면 그 내용을 반영해 다음 단계로 진행한다. 발견되지 않으면 자동으로 계속 진행한다.

## 5. [게이트 2] 외부 커넥터·비용 신호 확인
문서 텍스트에서 실제 외부 서비스명(OpenAI, Anthropic API, AWS, GCP, Azure, Stripe 등 구체적인
서비스/제품명)을 스캔한다. 발견되면 `harness/connectors.md`에 추가할 connector 안(용도·접근
도메인)을 텍스트로 제시하고, 다음 확인을 받을 때까지 그 connector를 실제로 추가하지 않는다
(AskUserQuestion 사용):

> "[서비스명]을 실제로 호출하는 기능으로 보입니다. harness/connectors.md에 connector로 추가하고
> 실제 API를 쓰는 걸로 진행할까요, 아니면 mock/규칙 기반으로 시작할까요?"

승인되면 `docs/decisions/ADR-000-template.md`를 복제해 `상태: accepted`로 이 결정을 기록한 뒤
`harness/connectors.md`에 반영한다(`docs/decisions/ADR-006-import-navendor-prd-frd-and-real-api.md`
패턴을 그대로 따른다). 발견되지 않으면 이 단계는 건너뛰고 자동으로 계속 진행한다.

## 6. 미정 스캔 → ADR-proposed 자동 초안
문서 전체에서 "미정", "TBD", "확인 필요", "OQ-", "Open Question" 패턴을 스캔한다. 매칭되는
항목마다:
1. `docs/decisions/adr-index.md`에서 다음 사용 가능한 ADR 번호를 확인한다(기존 최댓값 + 1).
2. `docs/decisions/ADR-000-template.md`를 복제해 `docs/decisions/ADR-0XX-<짧은-슬러그>.md`를
   만든다.
3. `상태: proposed`로 두고, "맥락" 절에 원문 출처(문서명 + 인용 구절)를 그대로 인용한다.
4. "대안"·"결정"·"근거" 절에는 최소 1개의 임시 동작 후보를 제안하되(비워두지 않는다), 그 결정이
   `proposed` 상태이며 Human PM 승인 전까지는 임시 동작으로만 취급됨을 명시한다
   (`docs/decisions/ADR-007-faq-fallback-when-no-evidence.md` 패턴 참고).
5. `docs/decisions/adr-index.md`에 한 행을 추가한다.

이미 같은 문서·같은 인용 구절에 대한 ADR이 `adr-index.md`에 존재하면(제목 또는 "맥락" 절 인용문
비교) 새로 만들지 않고 건너뛴다(멱등성).

## 7. traceability 골격 갱신
`docs/traceability.md` 매트릭스에 2~3단계에서 뽑은 요구사항마다 행을 추가한다: 요구사항 ID,
기준 문서(`requirements/<파일명>`), Task는 `-`, 도메인, 코드/PR은 `-`, 테스트·검증은 `-`, 상태는
`-`. 이미 같은 요구사항 ID 행이 있으면 건너뛴다(멱등성).

## 8. 도메인 스캐폴드 생성 (없는 도메인만)
3단계에서 태깅된 도메인마다:
- `loops/{domain}.loop.yaml`이 없으면, 이미 존재하는 다른 도메인 loop 파일
  (`loops/backend.loop.yaml`, `loops/frontend.loop.yaml`, `loops/ai.loop.yaml` 중 하나) 구조
  (target/trigger/action/verify/record 5요소)만 복사하고 내용을 그 도메인에 맞게 고쳐 쓴다.
  AI 도메인이고 구체적으로 어떤 성격의 AI 기능인지(RAG/분류/예측/추천)를 문서에서 판별할 수
  있으면 verify.gates를 그 성격에 맞는 지표로 채우고, 판별 안 되면 "미정 — 6단계에서
  ADR-proposed로 이미 에스컬레이션됨" 주석만 남긴다(지어내지 않는다).
- `agent-specs/{domain}-worker.spec.md`가 없으면 마찬가지로 기존 spec 구조(책임/권한/절차/금지)를
  복사해 도메인명만 바꾼다.
- 이미 파일이 있으면 절대 덮어쓰지 않는다(사람이 그 사이 손으로 고쳤을 수 있다).
- 새로 만든 spec이 있으면 `python3 scripts/generate_agents.py`를 실행해 `.claude/agents/`에
  반영하고, `harness/permissions.policy.md` · `.claude/hooks/enforce_permissions.py`의 POLICY
  미러에도 새 worker 행을 추가한다.

## 9. Sprint-01 후보 작성
우선순위가 "필수/must"인 요구사항 중, 도메인 하나당 **가장 작고 하나로 완결되는 조각 하나**를
고른다(여러 기능을 한 Sprint에 욱여넣지 않는다 — 예: AI 기능 5개가 있으면 그중 가장 단순한 1개만).
`plans/_sprint.template.md`, `plans/_task.template.md`를 복제해 `plans/sprint-01.md` +
`plans/task-001.md`(도메인이 여럿이면 도메인당 Task 1개, 번호를 이어 붙임)를 **상태: planned**로
작성한다. `plans/sprint-index.md`, `plans/task-index.md`에 행을 추가한다.

`plans/sprint-01.md`가 이미 있으면(이미 이 하네스를 한 번 부트스트랩한 적 있으면) 새로 만들지
않고 "이미 sprint-01이 존재합니다 — plans/sprint-02.md 후보로 제안할까요?"라고 확인을 구한다.

## 10. 실행 기록
`docs/harness-log.md`에 새 항목을 추가한다 — 어떤 문서를 읽었고, 몇 개 요구사항/도메인/
ADR-proposed/Sprint를 만들었는지, 4·5단계 게이트가 발동됐는지.

## 11. 요약 보고
사람에게 다음을 보고하고 종료한다: 도메인별 요구사항 수, 생성된 ADR-proposed 목록(번호+제목),
Sprint-01 제안 내용과 그 Definition of Done, 4·5단계에서 대기 중이었던 확인 사항과 그 처리 결과.

## 정직한 한계
텍스트 패턴 기반 절차이므로 표 형식이 아니거나 ID 컨벤션이 특이한 문서는 요구사항을 놓칠 수
있다. `docs/traceability.md`의 "커버리지 점검 질문"이 사람이 나중에 잡아내는 안전망 역할을 한다.
