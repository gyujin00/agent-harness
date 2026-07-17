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

## [2026-07-17] ai · T-001 · goal_loop (verify)
- action: FR-017 FAQ RAG 파이프라인(worktree `.worktrees/ai-T-001`, 브랜치 `ai/T-001-fr-017-faq-rag`,
  커밋 `e8d304a`~`9ce9f1c`)에 대한 독립 verify. work ≠ verify 원칙에 따라 ai-worker의 자체 실행 결과를
  신뢰하지 않고 전부 재실행함.
- verify:
  1) **eval 게이트**(`eval/run-eval.py` 실제 실행, 실 OpenAI API 비용 발생): retrieval_at_k 0.8889
     PASS(기준 0.80) / faithfulness 1.0000 PASS(기준 0.85) / answer_relevancy 1.0000 PASS(기준 0.80).
     `eval/thresholds.yaml` 기준선 대비 전부 통과. (참고: retrieval_at_k 8/9=0.8889는 정합적 — 9번
     샘플이 BR-007 무근거 케이스라 gold_chunk_ids=[]이며 정의상 이 항목의 retrieval_at_k는 항상 0이
     되므로, 8개 실답변 샘플이 전부 정답 청크를 회수했다는 뜻.)
     환경 메모(정책 판정에는 영향 없음): 기본 Windows 콘솔(cp949)에서 `python eval/run-eval.py`를
     그대로 실행하면 마지막 성공 출력의 em-dash(—) 문자 때문에 `UnicodeEncodeError`로 exit code 1을
     반환함 — `git diff main..HEAD -- eval/run-eval.py`로 확인 결과 이 줄은 T-001 이전 원본 스캐폴드에
     이미 있던 코드로 T-001이 만든 회귀가 아님. `PYTHONIOENCODING=utf-8`로 재실행하면 exit code 0,
     동일 점수로 정상 종료 확인. CI가 exit code만으로 게이트를 판정한다면 Windows 기본 로케일에서
     오탐 FAIL을 낼 수 있어 별도 개선 과제로 남김(이번 verify 대상 코드 밖).
  2) **eval-set 진위 확인**: `eval/rag-eval-set.jsonl` 9문항 중 4개(q001/prd-0006, q003/prd-0006+
     frd-0037, q007/frd-0020, q008/frd-0062+frd-0030)를 무작위 추출해 `ai/corpus/chunks.json`의 실제
     청크 텍스트와 대조 — 모두 expected_answer를 그대로 뒷받침함(예: q008의 "등록이 거부되고 사유가
     안내된다"는 frd-0062의 AC-002 원문과 정확히 일치). q009(계약 갱신 알림 며칠 전 발송)는 진짜
     무근거(no-evidence) 케이스임을 확인 — `requirements/` 전체에 "계약 갱신/갱신 알림/계약 만료" 관련
     문구가 전무(grep 0건). SRM 시스템에 그럴듯하게 인접하지만 실제로 범위 밖인 질문이라 무의미한
     gibberish 테스트가 아님. PASS.
  3) **BR-007 스팟체크**: `requirements/frd.md` BR-007 원문("근거 문서가 없거나 검색 결과가 없으면
     답변을 생성하지 않고 근거 없음을 표시한다") 확인. `ai/pipeline.py`/`ai/generation.py` 직접 読 —
     노이즈 플로어(cosine<0.22 조기 차단) + LLM sentinel(NO_EVIDENCE, `_looks_like_sentinel`로 견고화)
     2단 게이트가 실제 도달 가능한 코드로 구현돼 있음(죽은 코드/주석 아님). eval-set에 없는 질문 3개를
     직접 실행: "오늘 점심 뭐 먹을까요?"(완전 무관 주제) → 정상 폴백, "실시간 ERP 연동은 어떻게
     처리되나요?"(SRM 인접·범위 밖, 모듈 docstring이 스스로 언급한 어려운 케이스) → 정상 폴백(노이즈
     플로어가 아니라 LLM sentinel 레이어에서 정확히 판단), "공급업체 평가 등급은 어떻게 산정되나요?"
     (범위 내) → 근거 청크 5개 회수 + 올바른 등급 구간 답변. 3/3 기대대로 동작. PASS.
  4) **doc-verify(Sprint/Task 일치)**: `plans/task-001.md` DoD 대조. T-001 고유 커밋 3개
     (`e8d304a`/`3a4b9fd`/`9ce9f1c`)만 분리해 diff 확인 — 건드린 파일은 `ai/**`, `ai/prompts/**`,
     `eval/rag-eval-set.jsonl`, `eval/run-eval.py`, 그리고 상태 필드만 바뀐 `plans/task-001.md`,
     `plans/task-index.md`, `docs/traceability.md` — Scope 위반 0건(`backend/`, `frontend/` 등 범위
     밖 접근 없음). `run_pipeline`/`score_faithfulness`/`score_answer_relevancy`에 `NotImplementedError`
     스텁 잔존 0건(grep 확인). eval-set에 무근거 케이스 1건 포함 및 통과 확인(2번 항목). PR 설명/커밋
     메시지에 self-eval 승인 주장 없음(`eval/run-eval.py` 자체 docstring이 "공식 판정은 verifier가
     한다"고 명시) — self-eval 없음 조건 충족. `ai.loop.yaml`의 verify.gates(retrieval@k/faithfulness/
     answer_relevancy 기준선) 전부 통과(1번 항목). PASS.
- **판정: PASS.** 4개 게이트 전부 통과. `docs/traceability.md`의 FR-017 행을 in_verify로 갱신(record/PR
  단계는 verifier 소관 밖이라 미변경).
- 다음 루프에 넘길 컨텍스트: record 단계(PR 생성 + `docs/harness-log.md`에 record 기록)가 남음 —
  orchestrator/ai-worker가 이어감. eval 스크립트의 Windows 콘솔 인코딩 취약점(위 1번 항목)은 T-001
  범위 밖 기존 결함이라 별도 후속 과제로 남기되, 자동화(CI)에서 exit code를 그대로 신뢰한다면 우선순위
  있게 다뤄야 함.

## [2026-07-17] ai · T-001 · goal_loop (record)
- action: verify PASS 이후 record 단계 마감. `docs/traceability.md` FR-017 행을 `in_verify` →
  `done`으로, `코드/PR` 칸을 `PR #2`로 갱신. `plans/task-001.md` 상태 `in_progress` → `done`,
  `plans/task-index.md`에 verify 결과(PASS 수치) 반영. `plans/sprint-01.md` 상태 `active` → `done`,
  DoD 4개 항목 전부 체크, Open Issues의 OQ-006/OQ-010을 해소됨으로 표시(FR-014만 이월). Sprint-01의
  DoD 4번("verifier FAIL→back_to_action→재시도→PASS")이 계획대로 정확히는 일어나지 않았다는 점
  (실제로는 code-quality reviewer가 answer_relevancy 스코어러 설계 결함을 잡아 재작업시켰고, verifier
  공식 판정은 최초 1회에서 바로 PASS)을 `plans/sprint-01.md`에 "정직한 기록"으로 남김 — 완료를
  과장하지 않는다는 이 프로젝트의 원칙에 따름.
- record: PR #2 (`ai/T-001-fr-017-faq-rag` → `main`). Sprint-01 종료.
- 다음 루프에 넘길 컨텍스트: FR-017 하나로 a→b→c 통제 사이클(문제 발견→하네스 승격→자동 재발
  방지)의 처음 두 단계(a: 구현→검증, b: 문제를 게이트로 승격 — 이번엔 code-quality review가 그 역할)는
  실증됐다. c(다음에 같은 문제가 생기면 사람 지시 없이 루프가 스스로 재작업)는 아직 실증되지 않았음 —
  `loops/ai.loop.yaml`의 `trigger: eval.score.regressed` 신호가 실제로 뭔가에 연결되어 있지 않고
  여전히 문서상의 선언뿐이라, 다음 후속 과제로 "eval 회귀를 실제로 감지해 자동으로 이 loop를 재실행하는
  메커니즘"이 남아있다. 다음 Sprint 후보: FR-016/018/019/020 중 하나, 또는 이 자동 재실행 메커니즘
  자체.
