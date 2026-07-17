# HANDOFF.md — 코워크 이어작업 브리핑

이 폴더는 채팅에서 설계한 **하네스+루프 워크플로우 스캐폴드**입니다. 코워크에서 이어서 작업할 때 이 문서를 먼저 읽으세요.

## 이 저장소가 무엇인가
SRM 기능 저장소가 아니라, **백엔드·프론트엔드·AI(RAG/NLP)를 굴리는 작업 시스템 그 자체**입니다.
도메인 중립 이름(`agent-harness`)이라 SRM 외 과제로도 복제해 재사용할 수 있습니다.

## 핵심 설계 결정 (왜 이 구조인가)
1. **두 계층 분리** — 환경(Harness engineering) = 무엇을 주고 어떻게 통제할지 / 실행(Loop engineering) = 무엇을 반복시킬지.
   - 환경: `harness/`, `.claude/`, `eval/`, `docs/`
   - 실행: `loops/*.loop.yaml` (target → trigger → action → verify → record)
2. **work ≠ verify** — worker가 만든 결과는 절대 자기가 검증하지 않고, 별도 `verifier`가 판정한다.
3. **사람 → orchestrator → worker** — 사람은 worker에게 직접 프롬프트하지 않고 orchestrator가 위임한다.
4. **AI 도메인만 특별** — BE/FE의 verify는 test pass/fail로 끝나지만, RAG는 통과 기준을 사람이 못 만들어서
   `eval/`이 verify를 대신한다(정답셋으로 retrieval@k·faithfulness·answer_relevancy를 재고 `thresholds.yaml` 기준선과 비교).
5. **단일 원본 → 파생** — 손편집은 `AGENTS.md`, `harness/*`, `agent-specs/*.spec.md`, `loops/*.loop.yaml`, `eval/*`만.
   Git이 유일한 컨텍스트 원본(두 계정 토큰 한도 대응).

## 폴더 지도
```
agent-harness/
├── AGENTS.md              헌법(단일원본) → CLAUDE.md 파생
├── harness/               connectors · permissions.policy · worktree
├── loops/                 _loop.schema + backend/frontend/rag.loop
├── eval/                  thresholds · rag-eval-set · run-eval.py (AI verify)
├── agent-specs/           orchestrator · backend/frontend/rag-worker · verifier
├── requirements/          PRD/FRD (Na-Vendor에서 임포트, 손편집 금지 — ADR-006)
└── docs/                  harness-log · agent-control-log · decisions/ADR
```

## 지금까지 안 된 것 (= 코워크에서 할 다음 작업)
1. ~~`agent-specs/*.spec.md` → `.claude/agents/` 생성 스크립트 작성.~~ ✅ 완료 (`scripts/generate_agents.py`, 2026-07-17)
2. ~~`.claude/hooks/`에 `harness/permissions.policy.md`를 강제하는 PreToolUse hook 구현.~~ ✅ 완료 (`.claude/hooks/enforce_permissions.py` + `.claude/settings.json`, 2026-07-17)
3. `eval/run-eval.py`의 `run_pipeline` + 두 스코어러(faithfulness, answer_relevancy)를 실제 `ai/` 파이프라인에 연결
   (현재 `NotImplementedError`로 비어 있음).
4. ~~target 기준 파일 배치: `openapi.yaml`(backend 계약), `design-tokens.json`(frontend).~~ ✅ 완료 (스켈레톤, 2026-07-17) — `backend/`, `frontend/`, `ai/`, `ai/prompts/` 폴더도 README 스켈레톤과 함께 배치
5. `eval/rag-eval-set.jsonl`의 SRM 예시 문항을 실제 도메인 문항으로 교체.

## 2차 미팅 피드백 반영 (2026-07-17)

이사님 피드백의 핵심 4개를 기존 2계층 구조에 흡수함 (번호 폴더 전면 재구조화는 하지 않음).

1. **Sprint/Task 계획 계층** — `plans/`(sprint-index·task-index·템플릿). orchestrator가 목표를
   Sprint→Task로 점진 분해, Task가 도메인 loop를 트리거. (AGENTS.md §3.5)
2. **문서 검증** — `harness/verification.policy.md`(산출물별 검증 기준 단일 원본, 코드+AI생성문서).
   verifier.spec.md에 doc-verify 게이트 추가.
3. **추적성** — `docs/traceability.md`(요구사항→문서→Task→코드→테스트).
4. **현재 상태** — `docs/project-state.md`(사람이 보는 진행 단면).

권한 변경: orchestrator가 `plans/`·`agent-control-log.md` 쓰기 가능(계획 관리가 본업),
verifier가 `traceability.md` 쓰기 가능. hook POLICY 미러 동기화 완료.

## 평가 산출물 3종 착수 (2026-07-17, 과제 PDF §6)

완성도가 아니라 과정·통제·근거가 평가 대상. docs/에 3종을 채웠다.
- ① `docs/agent-control-journal.md` — 목표·맥락·제약·프롬프트·판단·교정 서사(회차 5건).
- ② `docs/harness-engineering-log.md` — 하네스 설계 '왜'와 시행착오 4건.
- ③ `docs/decisions/ADR-001~005` + `adr-index.md` — 실제 결정(대안·시행착오 포함).
- `docs/evaluation-map.md` — 평가기준↔산출물 매핑(발표용). ADR 템플릿도 대안/시행착오 필드로 보강.

## 코워크 첫 지시 예시
> 이 폴더의 HANDOFF.md와 README.md, AGENTS.md를 읽고 구조를 파악해줘.
> 그다음 "다음 작업" 1번(agent-specs → .claude/agents 생성 스크립트)부터 시작하자.
