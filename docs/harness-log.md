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
