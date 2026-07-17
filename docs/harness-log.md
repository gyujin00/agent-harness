# harness-log.md — 세션·검증 기록 (memory/state)

다음 루프가 읽어 컨텍스트를 잇는 단일 기록. verifier가 판정 결과를, worker가 작업 요약을 남긴다.

형식:
```
## [YYYY-MM-DD] {domain} · {issue-id} · {loop_kind}
- action: (무엇을 했나)
- verify: (게이트별 pass/fail, ai면 eval 점수)
- record: (PR 링크, ADR 번호)
- 다음 루프에 넘길 컨텍스트: (있으면)
```

---

## [예시] ai · 142 · goal_loop
- action: CSV 파일명 인코딩 처리 추가, 청크 정규화 보정
- verify: retrieval@k 0.82 PASS / faithfulness 0.87 PASS / answer_relevancy 0.81 PASS
- record: PR #158, ADR 없음
- 다음 루프에 넘길 컨텍스트: 없음

## [2026-07-17] harness · handoff-1 · goal_loop
- action: `scripts/generate_agents.py` 작성. agent-specs/*.spec.md 5개 → .claude/agents/*.md 5개 생성 (orchestrator, backend-worker, frontend-worker, rag-worker, verifier)
- verify: 수동 검토 5/5 PASS (frontmatter name/description/tools 매핑, 본문 보존 확인) · `--check` 모드 재실행 결과 변경 없음(멱등성 확인)
- record: PR 없음(로컬 작업, git 미초기화) · ADR 없음(가역적 스크립트 산출물)
- 다음 루프에 넘길 컨텍스트: HANDOFF "다음 작업" 2번(.claude/hooks/ PreToolUse로 permissions.policy.md 강제)부터 이어가면 됨

## [2026-07-17] harness · handoff-2 · goal_loop
- action: `.claude/hooks/enforce_permissions.py` 작성 + `.claude/settings.json`에 PreToolUse 등록.
  harness/permissions.policy.md의 경로(쓰기/읽기)·명령(배포/파괴적 명령) 권한을 코드화.
  agent_type 없는 메인 세션은 경로 제한 없이 통과, 공통 파괴적 명령(rm -rf/force push 등)만 차단.
- verify: 수동 시나리오 14건 실행 — 도메인 밖 쓰기 차단(4), 도메인 밖 읽기 차단(1), 배포/파괴적 명령 차단(3),
  verifier 전용 명령 차단(1), 정상 허용 경로(3), 관할 밖 subagent 통과(2) 전부 기대대로 동작(14/14 PASS).
  BLOCK 시 docs/agent-control-log.md 기록 확인 후 테스트 흔적은 삭제.
- record: PR 없음(로컬), ADR 없음
- 다음 루프에 넘길 컨텍스트: 알려진 한계(Bash 패턴 매칭 우회 가능, Grep/Glob path 미지정 시 미강제)는
  `.claude/hooks/enforce_permissions.py` 상단 docstring에 명시함. HANDOFF "다음 작업" 3번
  (eval/run-eval.py 파이프라인 연결)부터 이어가면 됨.

## [2026-07-17] harness · handoff-4 · goal_loop
- action: target 기준 파일 스켈레톤 배치. `openapi.yaml`(paths 빈 상태), `design-tokens.json`
  (placeholder 값) 생성. 도메인 폴더 `backend/`, `frontend/`, `ai/`, `ai/prompts/`를
  각각 README 스켈레톤과 함께 생성 (worker 작업 공간이 실제로 존재하도록).
  실제 API/파이프라인 구현은 하지 않음 — 사용자 요청에 따라 골격만 정리.
- verify: `yaml.safe_load`/`json.load`로 두 파일 파싱 확인. hook 재실행(backend-worker →
  backend/, openapi.yaml 쓰기 시나리오) 여전히 기대대로 동작 확인.
- record: PR 없음(로컬), ADR 없음
- 다음 루프에 넘길 컨텍스트: HANDOFF "다음 작업" 3번(run-eval.py 파이프라인 연결)과 5번
  (eval-set 실제 도메인 문항 교체)은 실제 백엔드/RAG 구현이 시작될 때 진행. 지금은 골격 단계.

## [2026-07-17] harness · pdf-review · goal_loop
- action: 업로드된 참고 PDF(클로드_코드_구조.pdf) 검토 → 공식 문서(code.claude.com/docs/en/hooks,
  /permissions, /memory) 대조 후 3가지 오류 확인(공식 hook 이벤트 목록이 4개뿐이라는 서술 오래됨/
  SessionStart를 비공식이라 잘못 서술, settings.json hooks 등록 예시가 실제 matcher/hooks/type
  스키마와 다름, permissions 예시 문법(`git:push`)이 실제 `Tool(specifier)` 문법과 다름).
  검토 중 발견한 개선점을 적용: `harness/permissions.policy.md`, `harness/worktree.md`에
  `paths:` frontmatter(backend/**, frontend/**, ai/**, loops/*.loop.yaml) 추가 후
  `.claude/rules/{permissions-policy,worktree,connectors}.md`로 심볼릭 링크 연결.
  `CLAUDE.md`의 harness/* 개별 `@import` 3줄 제거(중복 로드 방지, AGENTS.md만 import).
- verify: 심볼릭 링크 3개 모두 `readlink -f`로 원본(harness/*.md) 정상 해석 확인,
  `find .claude/rules -xtype l`로 끊어진 링크 없음 확인, frontmatter YAML 파싱 확인,
  CLAUDE.md 17줄(200줄 제한 내) 확인.
- record: PR 없음(로컬), ADR 없음(가역적 구조 변경 — CLAUDE.md만 되돌리면 원복 가능)
- 다음 루프에 넘길 컨텍스트: harness/connectors.md는 의도적으로 paths 스코프 없이 항상 로드.
  나중에 orchestrator 전용 컨텍스트로 옮길지는 별도 논의 필요.

## [2026-07-17] harness · mtg2-adopt · goal_loop
- action: 2차 미팅(이사님) 피드백 핵심 4개를 기존 2계층 구조에 흡수(개념만, 번호폴더 재구조화 안 함).
  (1) plans/ Sprint·Task 계획 계층 신설 + AGENTS.md §3.5. (2) harness/verification.policy.md
  검증기준 단일원본(코드+문서) 신설 + .claude/rules 심볼릭 링크 + verifier.spec doc-verify 게이트
  추가 후 agents 재생성. (3) docs/traceability.md 추적성 매트릭스. (4) docs/project-state.md 현재 단면.
  권한: orchestrator write에 plans/·agent-control-log.md 추가(잠재 불일치도 함께 해소),
  verifier write에 traceability.md 추가 → permissions.policy.md + hook POLICY 미러 동기화.
- verify: hook 신규+회귀 시나리오 10건 전부 기대대로(ALLOW 4 / DENY 6). 심볼릭 링크 4개 정상 해석,
  끊어진 링크 0, verification.policy frontmatter 파싱 OK, generate_agents --check 최신,
  전체 md frontmatter/loop yaml 파싱 OK, CLAUDE.md 15줄(<200). 테스트로 쌓인 BLOCK 로그는 정리.
- record: PR 없음(로컬), ADR 없음(가역적 구조 확장)
- 다음 루프에 넘길 컨텍스트: 이제 첫 Sprint를 plans/sprint-01.md로 정의하고 Task 1개를
  loop→verify→record까지 1회전 돌리면 전체 체계 실증이 됨(project-state.md의 미완 항목).

## [2026-07-17] harness · eval-artifacts · goal_loop
- action: 과제 PDF(§6) 평가 산출물 3종을 docs/에 채움. ADR-000 템플릿에 대안/시행착오 필드 보강 후
  이 세션의 실제 결정 5건을 ADR-001~005로 소급 작성(+adr-index). ① agent-control-journal.md(회차 5건 서사),
  ② harness-engineering-log.md(설계 근거·시행착오 4건·알려진 한계), evaluation-map.md(평가기준↔산출물 매핑).
  AGENTS.md §4를 실행기록(4.1)/평가산출물(4.2)로 분리. project-state·README·HANDOFF 반영.
- verify: 전체 md/yaml frontmatter 파싱 OK, generate_agents --check 최신, hook 회귀 3건 정상,
  ADR 6개+index 헤더 확인, 신규 문서 상호 링크(evaluation-map↔각 산출물) 일관성 확인.
- record: PR 없음(로컬), 결정은 ADR-001~005로 소급 기록됨.
- 다음 루프에 넘길 컨텍스트: 실제 SRM 범위(FR-01~05 중 1~2개) 선정 후 첫 Sprint 정의 →
  Task 1회전 실증이 남음. 그때 agent-control-journal에 회차 6을 이어 쓰면 됨.

## [2026-07-17] harness · navendor-import · goal_loop
- action: 사람이 별도 프로젝트 `Na-Vendor`(C:\dev\Na-Vendor)를 잠시 중단하고, 그 PRD/FRD 산출물만
  `agent-harness` 재구축의 요구사항 입력으로 재활용하기로 결정. 탐색 결과 Na-Vendor는 이미 12-agent
  파이프라인으로 FR-001~013 구현·리뷰를 마쳤고 FR-016~022 AI 기능도 ADR-009로 "실제 OpenAI API
  사용"을 확정해 둔, agent-harness보다 훨씬 앞선 별도 프로젝트임을 확인(AskUserQuestion 2회로 사람에게
  대상 저장소와 API 계승 여부 확인). 이에 따라: (1) `requirements/prd.md`, `requirements/frd.md`,
  `requirements/README.md` 신설(임포트 스냅샷, 손편집 금지) — AGENTS.md §0/§3.5, README.md, HANDOFF.md
  폴더 지도에 반영. (2) `docs/decisions/ADR-006-*.md` 작성 — PRD/FRD 재활용 근거 + Na-Vendor ADR-009
  (실제 OpenAI API) 계승 결정. (3) `harness/connectors.md`에 Embedding API(OpenAI)·LLM API(OpenAI)
  connector 2종 추가. (4) `eval/thresholds.yaml`의 `embedding_model`을 placeholder(`bge-m3`)에서
  `text-embedding-3-small`로, `llm_model: gpt-4o-mini` 신규 추가(ADR-006 근거).
- verify: 두 문서(prd.md/frd.md) 원본과 diff 없이 그대로 복사됐는지 라인 수 확인. AGENTS.md/README/
  HANDOFF/connectors.md/thresholds.yaml frontmatter·YAML 파싱 확인. adr-index.md에 ADR-006 행 추가 확인.
- record: PR 없음(로컬), ADR-006(accepted)
- 다음 루프에 넘길 컨텍스트: plans/sprint-01.md(FR-017 FAQ/RAG 목표)와 첫 Task 생성이 남음. FRD
  OQ-007~010(자연어 매핑·요약 규칙·등급조정 키워드·FAQ 폴백)은 여전히 미확정 — sprint-01 정의 시
  ADR-proposed로 병행 발의하고 AI 워크스트림은 막히지 않은 범위(corpus 구축, RAG 파이프라인 골격)부터
  진행.

## [2026-07-17] harness · generate-agents-baseline-fix · goal_loop
- action: `docs/superpowers/plans/2026-07-17-generic-harness-intake.md` 실행을 위해 worktree
  (`harness/generic-intake-framework`)에서 baseline 점검(`generate_agents.py --check`) 중 계획과
  무관한 기존 버그 2건 발견 후 수정. (1) `scripts/generate_agents.py`의
  `GENERATED_HEADER.format(source=source.relative_to(ROOT))`가 `.as_posix()` 없이 OS 네이티브
  구분자를 그대로 써서 Windows에서 `--check`가 5개 파일 전부를 가짜 STALE로 오판정하는 이식성
  버그 — `.as_posix()` 추가로 수정. (2) `.claude/agents/verifier.md`가 "mtg2-adopt" 세션에서
  "재생성 → 반영 확인"했다고 기록됐던 doc-verify 게이트 본문(판정 절차·record 절)이 실제로는
  누락된 채였던 실제 드리프트 — 수정된 스크립트로 재생성해 해소.
- verify: 5개 spec 전체 재생성 후 `--check` "모든 .claude/agents/*.md가 최신 상태입니다." 확인.
  `verifier.md`에 "판정 절차"·"## record" 문자열 존재 확인(2건). 헤더 원본 경로가 5개 파일 전부
  forward-slash로 통일됨 확인. `git status --short` 결과 `scripts/generate_agents.py`와
  `.claude/agents/verifier.md`만 변경(나머지 4개는 원래도 정확했음 — 버그는 재작성 없이 --check
  단계에서만 오판정을 냈던 것으로 확인).
- record: PR 없음(로컬, worktree 안에서 커밋 예정), ADR 없음(가역적 버그 수정)
- 다음 루프에 넘길 컨텍스트: 이 수정을 커밋한 뒤 본 계획(rag-worker→ai-worker 리네임, /intake
  커맨드 신설)을 Subagent-Driven으로 이어간다.

## [2026-07-17] harness · rag-to-ai-rename · goal_loop
- action: `rag-worker`/`loops/rag.loop.yaml`을 `ai-worker`/`loops/ai.loop.yaml`로 리네임하고
  일반화(agent-specs, loops, permissions.policy.md, hook POLICY 미러, generate_agents.py
  TOOLS_MAP, AGENTS.md, orchestrator.spec.md, HANDOFF.md, ai/README.md 등 전체 참조 갱신).
  `docs/superpowers/specs/2026-07-17-generic-harness-intake-design.md` 컴포넌트 A 실행.
- verify: hook 시나리오 2건(ai-worker의 backend/ 쓰기 차단, ai/prompts/ 쓰기 허용) 기대대로 동작.
  `generate_agents.py --check` 최신 확인. 전체 grep으로 rag-worker/rag.loop 잔존 참조 0건(역사
  기록 및 계획 문서 자체 제외) 확인. `docs/decisions/ADR-002-enforce-permissions-via-hook.md`의
  "rag-worker는 backend/를 건드리지 마" 언급은 실제 파일 경로 참조가 아니라 예시 문구여서(ADR-006/007과
  달리 깨지는 링크가 없음) 갱신 대상에서 제외함 — 사람 확인됨.
- record: PR 없음(로컬 커밋), ADR 없음(가역적 리네임)
- 다음 루프에 넘길 컨텍스트: `.claude/commands/intake.md` 신설이 남음(같은 설계 문서 컴포넌트 B).

## [2026-07-17] harness · intake-idempotency-check · goal_loop
- action: `/intake` 커맨드의 멱등성 검증(plan Task 6). 기존 `requirements/prd.md`/`frd.md`(navendor-import
  세션에서 처리됨, 실제 Sprint/Task/ADR/traceability 산출물이 이미 존재하는 상태)를 대상으로 `/intake` 재실행
  시나리오를 읽기 전용으로 분석. 파일 쓰기 없음 — `git status --short` 공집합 확인.
- verify: 요구사항 추출(step 2), 도메인 태깅(step 3) PASS. 다운스트림 멱등성(steps 6, 7, 9 — ADR
  중복제거, traceability 스켈레톤, Sprint-01 후보)도 기존 상태를 정확히 감지하고 스킵/분기 동작 예상 PASS.
  게이트 검사(steps 4, 5)에서는 UX 마찰 발견(안전성/정확성 버그 아님): 멱등성 판정이 post-/intake 형식으로
  기록된 해결책만 인식하는데, 수동 pre-/intake 세션(navendor-import 기록, ADR-006 accepted, connectors.md
  구성)은 이 형식 없이 이미 결정됨. 따라서 재실행 시 이미 응답한 AskUserQuestion 2건이 중복 발동할 가능성. 그러나
  중복/덮어쓰기/손상은 발생하지 않음 — 사용자가 다시 yes 하면 정상 진행.
- record: PR 없음(읽기 전용 검증), ADR 없음
- 다음 루프에 넘길 컨텍스트: 게이트 멱등성 검사를 "accepted ADR 존재" + "기술 harness-log 항목 패턴(navendor-import
  스타일)" 도 인식하도록 확장하는 것이 좋은 향후 개선 후보. 그러나 safety/correctness 측면에서는 블로커 아님 —
  plan 항목 7~9(Sprint-01 정의, Task 1회전)는 이 제약 하에서도 즉시 진행 가능.
