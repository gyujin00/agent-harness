# ADR-006: Na-Vendor PRD/FRD를 요구사항으로 재활용하고, FR-016·017·018·020의 실제 OpenAI API 사용 결정을 계승한다

- 상태: accepted
- 날짜: 2026-07-17
- 도메인: harness
- 관련 루프/문서: `requirements/prd.md`, `requirements/frd.md`, `harness/connectors.md`,
  `eval/thresholds.yaml`, `loops/rag.loop.yaml`, `agent-specs/rag-worker.spec.md`

## 맥락

`Na-Vendor`(`C:\dev\Na-Vendor`)는 이 저장소(`agent-harness`)와는 별도의, 이미 상당히 진행된
프로젝트였다 — 자체 12-agent 파이프라인으로 SRM MVP의 must 요구사항(FR-001~013)을 구현·리뷰까지
마쳤고(PR #45 governance 통합이 리뷰 대기 중), FR-016~022(AI 보조 기능)에 대해서도 이미 ADR-009로
"실제 OpenAI API 사용"을 확정해 둔 상태였다.

사람(Human PM)이 Na-Vendor 프로젝트 자체는 잠시 중단하고 `agent-harness` 위에서 새로 만들기로
결정했다. 다만 Na-Vendor의 PRD/FRD는 처음부터 다시 쓰지 않고 그대로 재활용하기로 했다 — RFP 분석,
페인포인트, REQ/FR 번호 체계, Human PM의 과거 확인 이력(guardrail 승인 등)이 이미 그 문서 안에
축적돼 있기 때문이다.

이때 두 가지가 확정되지 않은 채 남아 있었다:
1. PRD/FRD를 이 저장소 어디에 어떤 성격(손편집 대상 vs 임포트 스냅샷)으로 둘 것인가.
2. FR-016·017·018·020의 "실제 OpenAI API 사용"이라는, Na-Vendor에서 이미 내려진 결정을 그대로
   이어받을 것인가, 아니면 agent-harness 자체적으로 다시 mock/규칙 기반부터 재검토할 것인가 — 이는
   `harness/connectors.md`에 새 외부 connector를 추가하는 일이자(통제 범위 확대), 실제 비용·API
   키 관리가 발생하는 되돌리기 어려운 선택이라 Human PM에게 직접 확인했다.

## 대안

**(문서 위치)**
- (A) PRD/FRD를 `docs/` 하위 기존 구조(harness-log 등과 동일 폴더)에 섞어 둔다.
- (B) 새 `requirements/` 최상위 폴더를 만들어 "임포트된 요구사항 스냅샷"이라는 별도 카테고리로
  분리한다. — Human PM 선택.
- (C) 저장소에 복사하지 않고 Na-Vendor 경로를 그대로 참조한다. — Na-Vendor가 삭제/이동되면 이
  저장소의 요구사항 근거가 함께 깨지므로 기각.

**(실제 API 채택 여부)**
- (A) Na-Vendor ADR-009를 그대로 계승 — 실제 OpenAI API(Embedding + Chat Completions) 사용.
  — Human PM 선택.
- (B) PRD 원래 확정이었던 mock/규칙 기반(A4/A5)으로 되돌아가 시작하고, 실 API 전환은 별도 ADR로
  나중에 재논의. — 초기 구현 난도는 낮지만, 이미 Na-Vendor가 검증한 근거(RAG corpus 구조,
  guardrail 문구 등)를 다시 mock으로 갔다가 또 되돌리는 이중 작업이 된다는 점에서 비선호.
- (C) 지금 결정하지 않고 sprint-01 정의 전에 별도 ADR로 먼저 확정. — Human PM이 이미 (A)로 답해
  즉시 확정 가능했으므로 채택하지 않음.

## 결정

- (B) `requirements/` 폴더 신설. `requirements/prd.md`, `requirements/frd.md`는 Na-Vendor 원본의
  스냅샷이며 **손편집하지 않는다** (`AGENTS.md` §0, `requirements/README.md`).
- (A) FR-016·017·018·020은 Na-Vendor ADR-009와 동일하게 **실제 OpenAI API**(Embedding API + Chat
  Completions API)를 사용한다. `harness/connectors.md`에 두 connector를 신설 추가했다. FR-019는
  Na-Vendor와 동일하게 규칙 기반(키워드 사전 매칭)을 유지한다 — ADR-009도 FR-019는 대상에서
  제외했었다.

## 근거

- PRD/FRD는 이미 사람 확인(guardrail 승인, REQ-016~022 우선순위 확정)을 거친 산출물이라 재작성
  비용 대비 재사용 이득이 크다. 다만 Na-Vendor의 실제 코드/ADR 이력까지 가져오면 "처음부터 다시
  만든다"는 재구축 취지가 흐려지므로, 문서(요구사항)만 가져오고 구현은 가져오지 않는다
  (`requirements/README.md` 원칙 절 참고).
- 실제 API 계승은 이미 한 번 검증된 방향을 재사용하는 것이라 "mock으로 시작했다가 다시 실 API로
  전환"하는 이중 ADR·이중 구현을 피한다. 대신 connector 확대(harness/connectors.md 원칙 "connector를
  늘리는 것은 곧 통제 범위를 늘리는 것")에 따라 `rag-worker`만 접근하도록 권한을 좁혀 유지한다
  (`harness/permissions.policy.md`는 이미 `ai/`, `ai/prompts/`로 rag-worker 쓰기 범위를 한정).

## 시행착오 / 검증

- Na-Vendor FRD 원문(§7 AI, §11 OQ)을 직접 대조해, "FR-016~022 전부 mock"이라는 최초 브리핑의
  전제가 최신 FRD 상태(ADR-009 정정 이후)와 어긋난다는 것을 먼저 확인했다 — 브리핑 당시 원문을
  읽지 않고 진행했다면 mock 가정으로 sprint-01을 잘못 설계할 뻔했다.
- Na-Vendor `PROJECT_STATE.md`/`workspaces/srm-service/PROJECT_STATE.md`를 읽어 Na-Vendor가
  agent-harness보다 훨씬 앞서 있다는 사실(FR-001~013 구현·리뷰 완료, PR #45 대기)도 확인 — 두
  프로젝트가 별개라는 점을 사람에게 먼저 확인받은 뒤에 이 ADR을 작성했다(`AskUserQuestion` 2회).
- eval/thresholds.yaml의 `embedding_model: bge-m3`는 이 결정과 충돌하므로 이어지는 Task(#5)에서
  실제 OpenAI embedding 모델로 갱신한다 — 이 ADR이 그 변경의 근거 문서다.

## 결과 / 영향

- 생성: `requirements/prd.md`, `requirements/frd.md`, `requirements/README.md`,
  `docs/decisions/ADR-006-import-navendor-prd-frd-and-real-api.md`.
- 변경: `AGENTS.md`(§0, §3.5), `README.md`, `HANDOFF.md`(폴더 지도), `harness/connectors.md`(AI
  connector 2종 추가).
- 후속 영향: `eval/thresholds.yaml`의 `embedding_model`을 실제 API 기준으로 갱신 필요(별도 커밋),
  `rag-worker`의 프롬프트/파이프라인 구현 시 실제 API 키 주입 경로(환경변수/시크릿 매니저)를
  `.claude/hooks`가 차단하지 않는지 확인 필요.
- 되돌리기 비용: 중간. mock으로 되돌리려면 `harness/connectors.md`의 connector 제거 + 별도 ADR +
  이미 실 API로 짠 프롬프트/파이프라인 재작성이 필요하다.
