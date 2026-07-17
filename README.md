# 하네스 + 루프 워크플로우 스캐폴드

SRM 기능 저장소가 아니라, **백엔드·프론트엔드·AI(RAG/NLP)를 굴리는 작업 시스템 그 자체**입니다.
도메인 중립 이름(`agent-harness`)이라 SRM 외 과제로도 복제해 재사용할 수 있습니다.

## 두 계층
- **환경 · Harness engineering** — 무엇을 주고 어떻게 통제할지. `harness/`, `.claude/`, `eval/`, `docs/`.
- **실행 · Loop engineering** — 무엇을 반복시킬지. `plans/`(Sprint·Task) + `loops/*.loop.yaml` (target→trigger→action→verify→record).

## 핵심 규칙 3가지
1. **work ≠ verify** — worker가 만든 결과는 별도 `verifier`가 `harness/verification.policy.md` 기준으로 판정.
2. **사람 → orchestrator → worker** — 사람은 worker에게 직접 프롬프트하지 않고, orchestrator가 목표를 Sprint→Task로 분해해 위임.
3. **모든 루프는 record로 끝난다** — `docs/harness-log.md`·`traceability.md`·`project-state.md` + 필요 시 ADR.

## 실행 가능한 공용 런타임

Claude Code와 Codex는 같은 `AGENTS.md`, Task Contract, loop, 검증 정책을 사용한다. 도구 차이는
`harness_runtime/providers/`의 얇은 CLI 어댑터에만 둔다.

```powershell
# 설치된 Git/Claude/Codex/GitHub CLI 확인 — 모델 호출 없음
python -m harness_runtime doctor

# Task Contract·loop·권한·컨텍스트 정합성 확인
python -m harness_runtime validate plans/task-001.md

# 실제 worktree·모델 호출 없이 양방향 실행 계획 확인
python -m harness_runtime run plans/task-001.md --worker claude --verifier codex --dry-run
python -m harness_runtime run plans/task-001.md --worker codex --verifier claude --dry-run

# todo 상태 Task의 실제 구현→검증→재시도→기록→Draft PR
python -m harness_runtime run plans/task-002.md --worker codex --verifier claude --create-pr
```

실제 run은 `queued → preparing → in_progress → in_verify → back_to_action | recording` 상태 머신을
따른다. 검증 통과 시 commit·push·Draft PR까지만 수행하며 merge와 deploy 명령은 런타임에 없다.
원시 CLI 출력은 `.harness/runs/`에 로컬로 남고, 검토 가능한 정제 증거는
`docs/runs/{run-id}/`에 기록된다.

## AI 도메인이 특별한 이유
백엔드/프론트의 verify는 test pass/fail로 끝나지만, AI(RAG)는 통과 기준을 사람이 못 만들어서
`eval/`이 verify를 대신한다 — 정답셋(`eval/rag-eval-set.jsonl`)으로 retrieval@k·faithfulness·
answer_relevancy를 재고 `eval/thresholds.yaml` 기준선과 비교한다.

## 단일 원본 → 파생
손으로 편집하는 곳 (Git이 유일한 컨텍스트 원본):
- `AGENTS.md` (헌법) → `CLAUDE.md` 파생 (`@import ./AGENTS.md`만)
- `harness/*` (connector·권한·worktree·검증정책) → `permissions.policy.md`, `worktree.md`, `verification.policy.md`는
  `.claude/rules/*` 심볼릭 링크로 파생, `paths:` frontmatter로 도메인 작업 시에만 로드
- `agent-specs/*.spec.md` → `.claude/agents/` 파생
- `plans/*` (Sprint·Task 계획, orchestrator 관리)
- `loops/*.loop.yaml` (`_loop.schema.yaml` 참조)
- `eval/*` (AI verify 기준)

임포트만 하고 손편집하지 않는 곳:
- `requirements/*` (PRD/FRD — 외부 프로젝트에서 가져온 요구사항 스냅샷, 갱신은 재복사+ADR)

## 폴더 지도
```
agent-harness/
├── AGENTS.md              헌법(단일원본) → CLAUDE.md 파생
├── README.md              이 문서 (유일한 온보딩 진입점)
├── harness/               connectors · permissions.policy · worktree
├── harness_runtime/       Task Contract → worker → verifier → retry → record → Draft PR 실행기
├── loops/                 _loop.schema + backend/frontend/ai.loop
├── eval/                  thresholds · rag-eval-set · run-eval.py (AI verify)
├── agent-specs/           orchestrator · backend/frontend/ai-worker · verifier
├── requirements/          PRD/FRD (외부 프로젝트에서 임포트, 손편집 금지 — ADR-006)
├── plans/                 Sprint·Task 계획 (sprint-index · task-index · 템플릿)
├── backend/ frontend/ ai/  도메인별 실제 코드 (worker 작업 공간)
├── scripts/               generate_agents.py 등 파생 스크립트
├── prompts/               Claude/Codex 공용 worker·verifier launch brief
├── tests/                 런타임 계약·권한·상태·provider·통합 회귀 테스트
├── .claude/               Claude Code 설정 (agents · commands · hooks · rules)
├── .codex/                Codex hook 설정
└── docs/                  harness-log · traceability · project-state · runs/ · decisions/ · evaluation/
```

## 평가 산출물 (과제 PDF §6 — 코드 외 핵심)
이 과제는 완성도가 아니라 **과정·통제·근거**를 본다. `docs/`가 곧 평가 대상이다.
- ① Agent 통제: `docs/evaluation/agent-control-journal.md`
- ② 하네스 엔지니어링: `docs/evaluation/harness-engineering-log.md`
- ③ 의사결정·시행착오: `docs/decisions/ADR-*` (`adr-index.md`)
- 평가기준↔산출물 매핑(발표용): `docs/evaluation/evaluation-map.md`

## 2차 미팅 피드백 반영 (무인화·드리프트 방지·재사용성)
- **Sprint/Task** (`plans/`): Task를 미리 다 만들지 않고 Sprint 수행하며 점진 생성.
- **문서 검증** (`harness/verification.policy.md`): 코드뿐 아니라 AI 생성 문서(도메인/API/ERD)도 원천 대조.
- **추적성** (`docs/traceability.md`): 요구사항→문서→Task→코드→테스트 연결.
- **현재 상태** (`docs/project-state.md`): 사람이 한눈에 보는 진행 단면.

## 지금 상태는 어디서 보나
이 문서는 구조 설명이 목적이라 상세 진행 체크리스트는 담지 않는다. "지금 어디까지 왔는지"는
항상 `docs/project-state.md`를 확인한다 — 새 세션·회의·인수인계의 진입점.

## 새 세션/다른 프로젝트에서 이 하네스를 시작하려면
1. `requirements/`에 PRD/FRD(또는 이에 준하는 개발 문서)를 넣는다.
2. `/intake` 슬래시 커맨드를 실행한다 — 요구사항 추출, 도메인 태깅, ADR-proposed 초안, Sprint-01
   후보까지 자동으로 만든다(`.claude/commands/intake.md`).
3. 막힌 지점(외부 구현 존재 신호·실제 API/비용 신호)에서만 확인 질문이 온다 — 나머지는 자동 진행.
4. 결과를 검토하고 Sprint를 승인하면 `plans/_task.template.md`의 frontmatter를 채운다.
5. `harnessctl validate`와 `run --dry-run`을 확인한 뒤 실제 run을 시작한다. 런타임이 격리 worker →
   독립 verifier → 재시도 → record → Draft PR까지 수행하고, 개발자가 검토 후 merge한다.
