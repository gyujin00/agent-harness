# 폴더 가독성 개선 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 루트 안내 문서 4개(`AGENTS.md`/`CLAUDE.md`/`HANDOFF.md`/`README.md`)의 중복을 없애고
(`HANDOFF.md`를 `README.md`에 흡수), `docs/`의 평가 산출물 3종을 `docs/evaluation/`으로 분리해
"실행 기록"과 "평가 산출물"을 폴더로 구분한다.

**Architecture:** hook/`permissions.policy.md`/`loops/*.loop.yaml`가 정확한 경로로 참조하는
파일·폴더(도메인 코드, `plans/`, `docs/harness-log.md`·`traceability.md`·`agent-control-log.md`,
계약 파일)는 전혀 건드리지 않는다. 순수 문서 재배치 + 참조 갱신만 수행하고, 각 단계마다 grep으로
끊어진 링크가 없는지 확인한다.

**Tech Stack:** Markdown, git(`mv`/`rm`), grep 기반 검증(이 저장소는 pytest 없음 — 기존 관례:
스크립트/grep으로 자체 검증).

---

## 참고: 이 계획이 다루는 파일

| 파일 | 처리 |
|------|------|
| `README.md` | 전체 재작성 (HANDOFF.md 고유 내용 흡수) |
| `HANDOFF.md` | 삭제 |
| `docs/agent-control-journal.md` | → `docs/evaluation/agent-control-journal.md` (git mv) |
| `docs/harness-engineering-log.md` | → `docs/evaluation/harness-engineering-log.md` (git mv) |
| `docs/evaluation-map.md` | → `docs/evaluation/evaluation-map.md` (git mv) |
| `docs/evaluation/README.md` | 신규 생성 |
| `AGENTS.md` | §4.2 세 경로 갱신 |
| `docs/project-state.md` | 평가 산출물 경로 갱신 (다른 항목은 건드리지 않음) |

**건드리지 않는 파일**: `AGENTS.md`의 나머지 절, `CLAUDE.md`, 도메인 폴더(`backend/`, `frontend/`,
`ai/`, `eval/`, `loops/`, `agent-specs/`, `harness/`), `plans/`, `requirements/`, `scripts/`,
`openapi.yaml`, `design-tokens.json`, `docs/harness-log.md`, `docs/traceability.md`,
`docs/agent-control-log.md`, `docs/decisions/`, `docs/superpowers/`, `.claude/`. 이 목록에 있는
파일에 `git status`가 어떤 변경이라도 보이면 스코프 위반이다.

---

### Task 1: `docs/evaluation/` 폴더 신설 + 파일 이동

**Files:**
- Create: `docs/evaluation/README.md`
- Move (git mv): `docs/agent-control-journal.md` → `docs/evaluation/agent-control-journal.md`
- Move (git mv): `docs/harness-engineering-log.md` → `docs/evaluation/harness-engineering-log.md`
- Move (git mv): `docs/evaluation-map.md` → `docs/evaluation/evaluation-map.md`

- [ ] **Step 1: 현재 상태가 깨끗한지 확인**

```bash
cd "C:\dev\agent-harness"
git status --short
```
Expected: `?? .agents/`와 `?? .codex/` 두 줄만 있거나 완전히 비어 있음 — 이 두 폴더는 이 계획과
무관한, 이 저장소에 이미 있던 다른 도구의 설정 폴더라 무시해도 된다(git에 추가하지 않는다). 그
외의 변경/미커밋 파일이 보이면 STOP하고 보고한다 — 이 계획은 깨끗한 상태에서 시작해야 한다.

- [ ] **Step 2: 폴더 생성 + git mv로 3개 파일 이동**

```bash
cd "C:\dev\agent-harness"
mkdir -p docs/evaluation
git mv docs/agent-control-journal.md docs/evaluation/agent-control-journal.md
git mv docs/harness-engineering-log.md docs/evaluation/harness-engineering-log.md
git mv docs/evaluation-map.md docs/evaluation/evaluation-map.md
git status --short
```
Expected: 3줄의 `R  docs/{old} -> docs/evaluation/{same-name}` 출력.

- [ ] **Step 3: `docs/evaluation/README.md`를 정확히 이 내용으로 생성**

```markdown
# docs/evaluation/ — 평가 산출물 3종 (과제 PDF §6)

완성도가 아니라 과정·통제·근거를 보는 산출물. `AGENTS.md` §4.2 참고.

- `agent-control-journal.md` — ① Agent 활용·통제 기록(서사)
- `harness-engineering-log.md` — ② 하네스 엔지니어링 기록(설계 근거·시행착오)
- `evaluation-map.md` — 평가기준↔산출물 매핑(발표용 인덱스)

ADR(③ 의사결정·시행착오)은 `../decisions/`에 있다 — 이미 잘 알려진 컨벤션이라 별도로 옮기지
않고 `docs/decisions/`에 유지한다.
```

- [ ] **Step 4: 이동된 파일들의 내부 상호 참조가 여전히 유효한지 확인**

```bash
cd "C:\dev\agent-harness"
grep -n "agent-control-journal\.md\|harness-engineering-log\.md\|evaluation-map\.md" docs/evaluation/*.md
```
Expected: 매치되는 줄들이 전부 경로 접두어 없는 파일명(bare filename)이거나 `docs/evaluation/`
접두어를 쓴다 — `docs/agent-control-journal.md`처럼 옛 경로를 그대로 쓰는 줄이 있으면 안 된다.
(참고: 옮겨진 세 파일이 서로를 파일명만으로 참조하던 부분은 같은 폴더로 함께 이동했으므로 그대로
유효하며 수정할 필요 없다 — 이 grep은 그 사실을 재확인하는 용도.)

- [ ] **Step 5: 커밋**

```bash
cd "C:\dev\agent-harness"
git add docs/evaluation/
git commit -m "$(cat <<'EOF'
Move evaluation-deliverable docs into docs/evaluation/

Groups agent-control-journal.md, harness-engineering-log.md, and
evaluation-map.md (the "평가 산출물 3종" per AGENTS.md §4.2) into their
own folder, separate from execution-record docs that stay at docs/
root (harness-log.md, traceability.md, agent-control-log.md,
project-state.md — all referenced by exact path in
permissions.policy.md / the PreToolUse hook, so they must not move).

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: `AGENTS.md` §4.2 경로 갱신

**Files:**
- Modify: `AGENTS.md`

- [ ] **Step 1: 정확히 이 블록을 교체한다**

old_string:
```
### 4.2 평가 산출물 (과제 PDF §6 "코드 외 핵심 산출물")
- `docs/agent-control-journal.md` — ① Agent 활용·통제 기록(목표·맥락·제약·프롬프트·판단·교정, 서사).
- `docs/harness-engineering-log.md` — ② 하네스 설계 근거·시행착오·개선 시도(정책의 '왜').
- `docs/decisions/ADR-XXX-*.md` + `adr-index.md` — ③ 의사결정·시행착오(대안·근거 포함). 되돌리기 어려운 결정.
- `docs/evaluation-map.md` — 평가기준 ↔ 산출물 1:1 매핑(발표용 인덱스).
```
new_string:
```
### 4.2 평가 산출물 (과제 PDF §6 "코드 외 핵심 산출물")
- `docs/evaluation/agent-control-journal.md` — ① Agent 활용·통제 기록(목표·맥락·제약·프롬프트·판단·교정, 서사).
- `docs/evaluation/harness-engineering-log.md` — ② 하네스 설계 근거·시행착오·개선 시도(정책의 '왜').
- `docs/decisions/ADR-XXX-*.md` + `adr-index.md` — ③ 의사결정·시행착오(대안·근거 포함). 되돌리기 어려운 결정.
- `docs/evaluation/evaluation-map.md` — 평가기준 ↔ 산출물 1:1 매핑(발표용 인덱스).
```

- [ ] **Step 2: 확인**

```bash
cd "C:\dev\agent-harness"
grep -n "docs/agent-control-journal\.md\|docs/harness-engineering-log\.md\|docs/evaluation-map\.md" AGENTS.md
```
Expected: 매치 없음(exit 1) — 전부 `docs/evaluation/` 접두어로 바뀌었어야 한다.

- [ ] **Step 3: 커밋**

```bash
cd "C:\dev\agent-harness"
git add AGENTS.md
git commit -m "$(cat <<'EOF'
Update AGENTS.md §4.2 paths for docs/evaluation/ move

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: `docs/project-state.md` 평가 산출물 경로 갱신

**Files:**
- Modify: `docs/project-state.md`

- [ ] **Step 1: 정확히 이 블록을 교체한다** (다른 절은 건드리지 않는다 — 이 파일에는 이번 작업과
무관한 오래된 내용도 있지만, 이번 Task의 스코프는 평가 산출물 경로 3줄뿐이다)

old_string:
```
## 평가 산출물 (과제 PDF §6) — 3종 착수
- [x] ① Agent 통제 기록 `docs/agent-control-journal.md`(회차 5건 서술)
- [x] ② 하네스 엔지니어링 기록 `docs/harness-engineering-log.md`(설계 근거·시행착오 4건)
- [x] ③ 의사결정 문서 `docs/decisions/ADR-001~005` + `adr-index.md`
- [x] 평가기준↔산출물 매핑 `docs/evaluation-map.md`(발표용)
```
new_string:
```
## 평가 산출물 (과제 PDF §6) — 3종 착수
- [x] ① Agent 통제 기록 `docs/evaluation/agent-control-journal.md`(회차 5건 서술)
- [x] ② 하네스 엔지니어링 기록 `docs/evaluation/harness-engineering-log.md`(설계 근거·시행착오 4건)
- [x] ③ 의사결정 문서 `docs/decisions/ADR-001~005` + `adr-index.md`
- [x] 평가기준↔산출물 매핑 `docs/evaluation/evaluation-map.md`(발표용)
```

- [ ] **Step 2: 확인**

```bash
cd "C:\dev\agent-harness"
grep -n "docs/agent-control-journal\.md\|docs/harness-engineering-log\.md\|docs/evaluation-map\.md" docs/project-state.md
```
Expected: 매치 없음.

- [ ] **Step 3: 커밋**

```bash
cd "C:\dev\agent-harness"
git add docs/project-state.md
git commit -m "$(cat <<'EOF'
Update project-state.md paths for docs/evaluation/ move

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: `README.md` 재작성 (HANDOFF.md 흡수) + `HANDOFF.md` 삭제

**Files:**
- Modify: `README.md` (전체 교체)
- Delete: `HANDOFF.md`

- [ ] **Step 1: `README.md` 전체 내용을 정확히 이것으로 교체한다** (주의: 아래는 바깥쪽이
4-backtick(````` ```` `````) 펜스다 — 안에 폴더 지도용 3-backtick 블록이 중첩돼 있으므로, 실제
`README.md` 파일에 쓸 때는 이 바깥쪽 4-backtick 두 줄은 빼고 그 안쪽 내용만 저장한다.)

````markdown
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
├── loops/                 _loop.schema + backend/frontend/ai.loop
├── eval/                  thresholds · rag-eval-set · run-eval.py (AI verify)
├── agent-specs/           orchestrator · backend/frontend/ai-worker · verifier
├── requirements/          PRD/FRD (외부 프로젝트에서 임포트, 손편집 금지 — ADR-006)
├── plans/                 Sprint·Task 계획 (sprint-index · task-index · 템플릿)
├── backend/ frontend/ ai/  도메인별 실제 코드 (worker 작업 공간)
├── scripts/               generate_agents.py 등 파생 스크립트
├── .claude/               Claude Code 설정 (agents · commands · hooks · rules)
└── docs/                  harness-log · traceability · project-state · decisions/ · evaluation/
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
4. 결과를 검토하고 Sprint를 승인하면, `plans/task-XXX.md`를 참고해 도메인 worker에게 위임 →
   verifier가 판정 → record로 이어간다.
````

- [ ] **Step 2: `HANDOFF.md` 삭제**

```bash
cd "C:\dev\agent-harness"
git rm HANDOFF.md
```

- [ ] **Step 3: 확인**

```bash
cd "C:\dev\agent-harness"
test -f HANDOFF.md && echo "FAIL: still exists" || echo "OK: deleted"
grep -c "." README.md
```
Expected: `OK: deleted`, 그리고 두 번째 명령은 0보다 큰 숫자(파일이 비어있지 않음을 확인).

- [ ] **Step 4: 커밋**

```bash
cd "C:\dev\agent-harness"
git add README.md
git commit -m "$(cat <<'EOF'
Absorb HANDOFF.md into README.md, delete HANDOFF.md

Single onboarding entry point instead of two overlapping docs. Current
status ("지금까지 안 된 것" checklist) is dropped rather than carried
over — it duplicated docs/project-state.md, which already owns that
role. Folder map and paths updated for the docs/evaluation/ move.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: 저장소 전체 완결성 검증

**Files:** (읽기만)

- [ ] **Step 1: 옛 경로/파일명이 예상 밖에 남아있지 않은지 확인**

```bash
cd "C:\dev\agent-harness"
grep -rl "HANDOFF\.md" --include="*.md" . \
  | grep -v "docs/harness-log.md" \
  | grep -v "docs/decisions/ADR-006" \
  | grep -v "docs/superpowers/plans/2026-07-17-generic-harness-intake.md" \
  | grep -v "docs/superpowers/specs/2026-07-17-generic-harness-intake-design.md" \
  | grep -v "docs/superpowers/plans/2026-07-17-folder-readability.md"
```
Expected: 매치 없음. (마지막 제외 항목은 이 계획 문서 자신 — "HANDOFF.md 삭제"라는 과거형 지시를
담고 있으므로 정상.) 뭔가 남아있으면 정확히 뭔지 보고하고, 계획에 없는 파일이면 직접 고치지 말고
질문한다.

```bash
cd "C:\dev\agent-harness"
grep -rl "docs/agent-control-journal\.md\|docs/harness-engineering-log\.md\|docs/evaluation-map\.md" --include="*.md" . \
  | grep -v "docs/harness-log.md" \
  | grep -v "docs/superpowers/plans/2026-07-17-generic-harness-intake.md" \
  | grep -v "docs/superpowers/plans/2026-07-17-folder-readability.md" \
  | grep -v "docs/superpowers/specs/2026-07-17-folder-readability-design.md"
```
Expected: 매치 없음. (제외 목록: `docs/harness-log.md`는 과거 세션 이력이라 손대지 않는 것이
이미 확립된 원칙, 이 계획/설계 문서 자신은 옛 경로를 설명 목적으로 인용하므로 정상.)

- [ ] **Step 2: hook POLICY가 이번에 옮긴 파일명을 참조하지 않는지 재확인** (안전 차원의 이중 확인
— 브레인스토밍 단계에서 이미 확인했지만, 실제로 옮긴 뒤 다시 확인한다)

```bash
cd "C:\dev\agent-harness"
grep -n "agent-control-journal\|harness-engineering-log\|evaluation-map" .claude/hooks/enforce_permissions.py harness/permissions.policy.md
```
Expected: 매치 없음 — 이 세 파일명은 애초에 hook/policy가 참조하지 않았어야 한다.

- [ ] **Step 3: `python scripts/generate_agents.py --check`로 이번 변경이 agent 파생물에 영향
없음을 재확인** (건드린 파일이 `agent-specs/`가 아니므로 영향 없어야 하는 회귀 확인)

```bash
cd "C:\dev\agent-harness"
python scripts/generate_agents.py --check
```
Expected: `모든 .claude/agents/*.md가 최신 상태입니다.` (참고: 이 환경에서는 `python3`가 아니라
`python`을 써야 PyYAML을 찾는다.)

- [ ] **Step 4: 최종 트리 확인**

```bash
cd "C:\dev\agent-harness"
ls
ls docs/
ls docs/evaluation/
git status --short
```
Expected: `HANDOFF.md`가 루트에 없음, `docs/evaluation/`에 4개 파일(3개 이동본 + README.md),
`docs/` 루트에는 `harness-log.md`/`traceability.md`/`agent-control-log.md`/`project-state.md`/
`decisions/`/`evaluation/`/`superpowers/`만 있음, `git status --short`는 `?? .agents/`/`?? .codex/`
(이 계획과 무관, Task 1 Step 1 참고) 외에는 비어 있음(전부 커밋됨).

- [ ] **Step 5: `docs/harness-log.md`에 이번 작업 기록 추가**

파일 끝에 추가(현재 마지막 항목이 어디서 끝나는지 먼저 `tail -20 docs/harness-log.md`로 확인한
뒤, 그 뒤에 이어 붙인다 — 중복/덮어쓰기 금지):

```markdown

## [2026-07-17] harness · folder-readability · goal_loop
- action: 루트 안내 문서 4개(AGENTS.md/CLAUDE.md/HANDOFF.md/README.md)의 중복 해소 —
  `HANDOFF.md`를 `README.md`에 흡수 후 삭제(상태 체크리스트는 `docs/project-state.md`와
  중복이라 버림, project-state.md가 이미 최신 상태를 갖고 있어 정보 손실 아님). `docs/`의 평가
  산출물 3종(agent-control-journal.md, harness-engineering-log.md, evaluation-map.md)을
  `docs/evaluation/`으로 이동. hook/permissions.policy.md가 참조하는 경로(도메인 폴더,
  `plans/`, `docs/harness-log.md`·`traceability.md`·`agent-control-log.md`, 계약 파일)는
  브레인스토밍 단계에서 명시적으로 범위 밖으로 제외해 건드리지 않음.
  `docs/superpowers/specs/2026-07-17-folder-readability-design.md` 참고.
- verify: 저장소 전체 grep으로 옛 경로/파일명 잔존 참조 0건(역사 기록·계획 문서 자체 제외) 확인.
  hook POLICY/permissions.policy.md가 이동 대상 파일명을 참조하지 않음(원래도 안 했음) 재확인.
  `generate_agents.py --check` 최신 확인(영향 없음, 기대대로).
- record: PR 없음(이 저장소는 로컬/PR 워크플로우 중 상황에 따라 결정), ADR 없음(가역적 문서 재배치)
- 다음 루프에 넘길 컨텍스트: 없음. 도메인 폴더 구조(backend/frontend/ai 3분할) 자체를 더 정리하고
  싶다면 별도 브레인스토밍이 필요(이번 범위 아님, `docs/superpowers/specs/2026-07-17-folder-readability-design.md`
  "정직한 한계" 절 참고).
```

- [ ] **Step 6: 커밋**

```bash
cd "C:\dev\agent-harness"
git add docs/harness-log.md
git commit -m "$(cat <<'EOF'
Record folder-readability work in harness-log

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Self-Review 체크리스트 (계획 작성자용, 실행 전 확인됨)

- **스펙 커버리지**: 설계 문서의 결정 A(HANDOFF→README 흡수) → Task 4. 결정 B(`docs/evaluation/`
  신설) → Task 1. 결정 C(참조 갱신) → Task 2·3, 검증은 Task 5. 전부 대응 확인.
- **플레이스홀더 스캔**: "TODO"/"TBD" 없음 — 모든 Step에 실행 가능한 정확한 명령/전체 파일 내용을
  넣었음(`README.md` 전체 텍스트, `docs/evaluation/README.md` 전체 텍스트 포함).
- **범위 일관성**: Task 1~5 전체에서 도메인 폴더·`plans/`·`docs/harness-log.md` 등 제외 목록을
  건드리는 Step이 없음을 재확인.
