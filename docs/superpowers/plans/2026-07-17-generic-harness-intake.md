# 범용 하네스 `/intake` 부트스트랩 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `rag-worker`를 도메인 중립적인 `ai-worker`로 일반화하고, `requirements/`에 어떤 프로젝트
문서를 넣든 `/intake` 한 번으로 Sprint-01·ADR-proposed·도메인 스캐폴드가 자동 생성되는 하네스
부트스트랩 커맨드를 추가한다.

**Architecture:** (A) 기존 RAG 전용 이름(`rag-worker`, `loops/rag.loop.yaml`)을 손으로 리네임 +
전체 참조 갱신. (B) `.claude/commands/intake.md`라는 프롬프트 기반 슬래시 커맨드를 신설해,
문서 읽기 → 도메인 태깅 → 2개 확인 게이트(외부 구현 존재/커넥터 비용) → ADR-proposed 자동 초안
→ traceability 골격 → 도메인 스캐폴드 생성 → Sprint-01 초안 → 기록 → 보고 순으로 진행한다.
검증은 이 저장소의 기존 관례(수동 시나리오 실행 + 결과를 harness-log.md에 기록)를 따른다 — 이
프로젝트에는 pytest 스위트가 없다.

**Tech Stack:** Python 3(hook/생성 스크립트), YAML(loop spec), Markdown(agent-specs/ADR/plans),
Claude Code `.claude/commands/*.md`(슬래시 커맨드).

---

## 참고: 이 계획이 다루는 파일

| 파일 | 처리 |
|------|------|
| `agent-specs/rag-worker.spec.md` | → `agent-specs/ai-worker.spec.md` (rename + 내용 일반화) |
| `loops/rag.loop.yaml` | → `loops/ai.loop.yaml` (rename + verify.gates 예시화) |
| `harness/permissions.policy.md` | rag-worker 행 → ai-worker |
| `.claude/hooks/enforce_permissions.py` | POLICY dict, WORKER_NAMES |
| `scripts/generate_agents.py` | TOOLS_MAP |
| `AGENTS.md` | 도메인 표 |
| `agent-specs/orchestrator.spec.md` | worker 목록 문구 |
| `HANDOFF.md`, `ai/README.md`, `ai/prompts/README.md` | 폴더 지도/참조 |
| `eval/run-eval.py`, `eval/thresholds.yaml` | 주석 참조 |
| `plans/sprint-01.md`, `plans/task-001.md`, `plans/task-index.md` | worker/loop 참조 |
| `docs/decisions/ADR-006-*.md`, `ADR-007-*.md` | 파일 경로 참조 |
| `.claude/commands/intake.md` | 신규 생성 (핵심 산출물) |
| `docs/harness-log.md`, `docs/project-state.md` | 작업 기록 |

**건드리지 않는 파일 (역사 기록이므로 그대로 둠)**: `docs/agent-control-log.md`,
`docs/agent-control-journal.md`, `docs/decisions/ADR-005-*.md`의 "결과/영향" 절 — 모두 그
시점에 실제로 있었던 사실의 기록이라 리네임 이후에도 고치지 않는다.

---

### Task 1: `rag-worker` → `ai-worker` 핵심 파일 리네임 + 일반화

**Files:**
- Rename: `agent-specs/rag-worker.spec.md` → `agent-specs/ai-worker.spec.md`
- Rename: `loops/rag.loop.yaml` → `loops/ai.loop.yaml`

- [ ] **Step 1: git mv로 두 파일을 리네임한다**

Run:
```bash
cd "C:\dev\agent-harness"
git mv agent-specs/rag-worker.spec.md agent-specs/ai-worker.spec.md
git mv loops/rag.loop.yaml loops/ai.loop.yaml
git status --short
```
Expected: `R  agent-specs/rag-worker.spec.md -> agent-specs/ai-worker.spec.md`,
`R  loops/rag.loop.yaml -> loops/ai.loop.yaml` 두 줄이 출력된다.

- [ ] **Step 2: `agent-specs/ai-worker.spec.md` 내용을 일반화한다**

파일 전체를 다음 내용으로 교체한다(Write 도구 사용):

```markdown
---
name: ai-worker
role: AI 파이프라인·프롬프트 구현 (work 전용)
generates: .claude/agents/ai-worker.md
loop: loops/ai.loop.yaml
---

# ai-worker

## 책임
- `ai/` 범위에서 AI 파이프라인(RAG, 분류, 추천, 예측 등 — 프로젝트마다 다름), 프롬프트
  (`ai/prompts/`)를 수정한다 (**action**만).
- 목표는 기능 추가가 아니라 **eval 점수 회귀 방지/개선**이다. 이 AI 기능이 구체적으로 무엇인지
  (RAG/분류/추천 등)와 그에 맞는 eval 지표는 `eval/thresholds.yaml`과 이 도메인을 생성할 때
  `/intake`(또는 사람)가 채워 넣은 값을 따른다 — 이 spec 자체는 특정 AI 기법을 전제하지 않는다.

## 권한 (permissions.policy.md)
- 쓰기: `ai/`, `ai/prompts/`
- 읽기: `ai/`, `eval/`, `docs/`
- 차단: `backend/`, `frontend/`, push/배포 명령

## 절차
1. 위임받은 이슈/목표(예: "환각 답변 증가", "추천 정확도 하락")를 격리 worktree에서 연다.
2. 파이프라인/프롬프트 수정.
3. **자기 자신이 eval을 돌려 판정하지 않는다.** verifier가 `eval/run-eval.py`로 판정.

## 결정 규약
- 임베딩 모델·청크 크기·Top-K·retriever 등 파이프라인 핵심 파라미터 변경은 **ADR 필수**.
  (`eval/thresholds.yaml`의 config 변경과 동반됨)
- 임베딩 차원 변경 시 Vector DB collection 재색인이 필요함을 ADR에 명시.

## 금지
- self-eval 승인.
- eval 정답셋(`eval/*-eval-set.jsonl`)을 점수에 맞추려고 수정하는 행위(치팅).
```

- [ ] **Step 3: `loops/ai.loop.yaml` 내용을 일반화한다**

파일 전체를 다음 내용으로 교체한다:

```yaml
# loops/ai.loop.yaml
# $ref: ./_loop.schema.yaml (loop.spec/v1)
# ★ 핵심 도메인: verify가 비결정적이라 eval 하네스(eval/)가 통과 기준을 대신한다.
# verify.gates는 예시다 — 실제 AI 기능 성격(RAG/분류/추천 등)에 맞는 지표로
# /intake(또는 사람)가 채워 넣는다. 성격이 불명확하면 지어내지 말고 ADR-proposed로 확인 요청.

target:
  paths:  [ai/]
  labels: ["area:ai"]
  extra:
    prompts:  [ai/prompts/]
    eval_set: [eval/]     # 실제 eval-set 파일명은 프로젝트마다 다름

trigger:
  - { type: human.goal,  detail: "AI 기능 목표 지정 → Goal loop" }
  - { type: signal,      detail: "새 데이터/문서 인제스트 → 재평가" }
  - { type: signal,      detail: "prompt/모델 변경 → 회귀 평가" }
  - { type: signal,      detail: "eval.score.regressed → 자동 개선 루프(Ops)" }

action:
  agent:    ai-worker
  worktree: true

verify:
  gates:                                   # 예시 (RAG인 경우) — eval/thresholds.yaml 기준선과 비교
    - "retrieval@k     >= thresholds.retrieval_at_k   (RAG: 검색 품질)"
    - "faithfulness    >= thresholds.faithfulness      (RAG: 환각 억제)"
    - "answer_relevancy >= thresholds.answer_relevancy (RAG: 답변 적합도)"
    - "분류/추천 등 다른 AI 성격이면 accuracy/precision/recall/MAE 등으로 대체 — thresholds.yaml에 정의"
    - "기준선 미달 → 실패로 판정하고 action으로 되돌림"
  verifier: verifier          # ai-worker가 자기 결과를 self-eval 하지 않음
  on_fail:  back_to_action

record:
  outputs: [PR, "eval 리포트 (before/after diff)"]
  memory:
    - docs/harness-log.md
    - "docs/decisions/ADR-XXX-*.md (임베딩 모델·청크 전략·Top-K·모델 변경 시)"
  required: true
```

- [ ] **Step 4: 커밋**

```bash
cd "C:\dev\agent-harness"
git add agent-specs/ai-worker.spec.md loops/ai.loop.yaml
git commit -m "$(cat <<'EOF'
Rename rag-worker/rag.loop.yaml to ai-worker/ai.loop.yaml

Generalizes the AI domain scaffold so it is not tied to RAG specifically,
per docs/superpowers/specs/2026-07-17-generic-harness-intake-design.md.
EOF
)"
```

---

### Task 2: 단일 원본 참조 갱신 (permissions.policy, hook, generate_agents, AGENTS.md, orchestrator.spec)

**Files:**
- Modify: `harness/permissions.policy.md`
- Modify: `.claude/hooks/enforce_permissions.py`
- Modify: `scripts/generate_agents.py`
- Modify: `AGENTS.md`
- Modify: `agent-specs/orchestrator.spec.md`

- [ ] **Step 1: `harness/permissions.policy.md`의 rag-worker 행을 ai-worker로 바꾼다**

old_string:
```
| rag-worker | `ai/`, `ai/prompts/` | `ai/`, `eval/`, `plans/`, `docs/` | `backend/`, `frontend/`, `plans/` 쓰기 |
```
new_string:
```
| ai-worker | `ai/`, `ai/prompts/` | `ai/`, `eval/`, `plans/`, `docs/` | `backend/`, `frontend/`, `plans/` 쓰기 |
```

- [ ] **Step 2: `.claude/hooks/enforce_permissions.py`의 POLICY dict와 WORKER_NAMES를 바꾼다**

old_string:
```python
    "rag-worker": {
        "write_allow": ["ai/", "ai/prompts/"],
        "read_allow": ["ai/", "eval/", "plans/", "docs/"],
    },
    "verifier": {
        "write_allow": ["docs/harness-log.md", "docs/traceability.md"],
        "read_allow": ["*"],
    },
}

WORKER_NAMES = {"backend-worker", "frontend-worker", "rag-worker"}
```
new_string:
```python
    "ai-worker": {
        "write_allow": ["ai/", "ai/prompts/"],
        "read_allow": ["ai/", "eval/", "plans/", "docs/"],
    },
    "verifier": {
        "write_allow": ["docs/harness-log.md", "docs/traceability.md"],
        "read_allow": ["*"],
    },
}

WORKER_NAMES = {"backend-worker", "frontend-worker", "ai-worker"}
```

- [ ] **Step 3: hook을 수동 시나리오로 즉시 검증한다 (리네임 후 정책이 여전히 강제되는지)**

Run:
```bash
cd "C:\dev\agent-harness"
echo '{"tool_name":"Write","tool_input":{"file_path":"C:/dev/agent-harness/backend/foo.py"},"agent_type":"ai-worker","cwd":"C:/dev/agent-harness"}' | python3 .claude/hooks/enforce_permissions.py
```
Expected: `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", ...}}` —
`ai-worker`가 `backend/`에 쓰려는 시도가 차단된다(이전에 `rag-worker`였다면 통과했을 이름 불일치
버그가 없는지 확인).

```bash
echo '{"tool_name":"Write","tool_input":{"file_path":"C:/dev/agent-harness/ai/prompts/faq.md"},"agent_type":"ai-worker","cwd":"C:/dev/agent-harness"}' | python3 .claude/hooks/enforce_permissions.py
```
Expected: 아무 출력 없이 종료(exit 0) — `ai-worker`가 `ai/prompts/`에 쓰는 건 정상 허용된다.

- [ ] **Step 4: `scripts/generate_agents.py`의 TOOLS_MAP을 바꾼다**

old_string:
```python
    "rag-worker": ["Read", "Write", "Edit", "Bash", "Grep", "Glob"],
```
new_string:
```python
    "ai-worker": ["Read", "Write", "Edit", "Bash", "Grep", "Glob"],
```

- [ ] **Step 5: `AGENTS.md` 도메인 표를 바꾼다**

old_string:
```
| AI (RAG/NLP) | `ai/` | `rag-worker` | 비결정적 → **eval 회귀** (`eval/`) |
```
new_string:
```
| AI | `ai/` | `ai-worker` | 비결정적 → **eval 회귀** (`eval/`) |
```

- [ ] **Step 6: `agent-specs/orchestrator.spec.md`의 worker 목록 문구를 바꾼다**

old_string:
```
3. 라벨/경로로 worker 결정: backend-worker | frontend-worker | rag-worker.
```
new_string:
```
3. 라벨/경로로 worker 결정: backend-worker | frontend-worker | ai-worker.
```

- [ ] **Step 7: 커밋**

```bash
cd "C:\dev\agent-harness"
git add harness/permissions.policy.md .claude/hooks/enforce_permissions.py scripts/generate_agents.py AGENTS.md agent-specs/orchestrator.spec.md
git commit -m "$(cat <<'EOF'
Point single-source policy/hook/generator files at ai-worker

Follow-up to the rag-worker -> ai-worker rename in Task 1.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: `.claude/agents/` 재생성 + CLAUDE.md 파생 확인

**Files:**
- Delete: `.claude/agents/rag-worker.md`
- Regenerate (via script): `.claude/agents/ai-worker.md`, `.claude/agents/orchestrator.md`

- [ ] **Step 1: 오래된 파생 파일을 지운다**

```bash
cd "C:\dev\agent-harness"
git rm .claude/agents/rag-worker.md
```

- [ ] **Step 2: 재생성 스크립트를 실행한다**

```bash
python3 scripts/generate_agents.py
```
Expected: 5줄의 `[OK] agent-specs/... -> .claude/agents/...` 출력, 그중
`[OK] agent-specs/ai-worker.spec.md -> .claude/agents/ai-worker.md`가 포함된다.

- [ ] **Step 3: `--check`로 멱등성을 확인한다**

```bash
python3 scripts/generate_agents.py --check
```
Expected: `모든 .claude/agents/*.md가 최신 상태입니다.` (exit 0)

- [ ] **Step 4: 새로 생성된 파일이 `rag-worker` 문자열을 전혀 포함하지 않는지 확인한다**

```bash
grep -ri "rag-worker" .claude/agents/*.md
```
Expected: 아무 결과 없음(exit 1, 매치 없음).

- [ ] **Step 5: 커밋**

```bash
git add -A .claude/agents
git commit -m "$(cat <<'EOF'
Regenerate .claude/agents/ after ai-worker rename

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: 나머지 문서 참조 갱신 (living docs + 이번 세션 SRM 계획 산출물)

**Files:**
- Modify: `HANDOFF.md`, `ai/README.md`, `ai/prompts/README.md`
- Modify: `eval/run-eval.py`, `eval/thresholds.yaml`
- Modify: `plans/sprint-01.md`, `plans/task-001.md`, `plans/task-index.md`
- Modify: `docs/decisions/ADR-006-import-navendor-prd-frd-and-real-api.md`, `docs/decisions/ADR-007-faq-fallback-when-no-evidence.md`

- [ ] **Step 1: `HANDOFF.md` 폴더 지도를 바꾼다**

old_string:
```
├── loops/                 _loop.schema + backend/frontend/rag.loop
├── eval/                  thresholds · rag-eval-set · run-eval.py (AI verify)
├── agent-specs/           orchestrator · backend/frontend/rag-worker · verifier
```
new_string:
```
├── loops/                 _loop.schema + backend/frontend/ai.loop
├── eval/                  thresholds · rag-eval-set · run-eval.py (AI verify)
├── agent-specs/           orchestrator · backend/frontend/ai-worker · verifier
```

- [ ] **Step 2: `ai/README.md`를 바꾼다**

old_string:
```
`rag-worker` 전용 작업 공간 (`harness/permissions.policy.md`: 쓰기 허용, `ai/prompts/` 포함).
```
new_string:
```
`ai-worker` 전용 작업 공간 (`harness/permissions.policy.md`: 쓰기 허용, `ai/prompts/` 포함).
```

old_string:
```
- 실행 루프: [`../loops/rag.loop.yaml`](../loops/rag.loop.yaml)
```
new_string:
```
- 실행 루프: [`../loops/ai.loop.yaml`](../loops/ai.loop.yaml)
```

- [ ] **Step 3: `ai/prompts/README.md`를 바꾼다**

old_string:
```
`loops/rag.loop.yaml`의 signal 트리거(`prompt 변경 → 회귀 평가`) 대상이다.
```
new_string:
```
`loops/ai.loop.yaml`의 signal 트리거(`prompt 변경 → 회귀 평가`) 대상이다.
```

- [ ] **Step 4: `eval/run-eval.py`의 docstring을 바꾼다**

old_string:
```
verifier sub-agent가 rag.loop.yaml의 verify 단계에서 호출한다.
```
new_string:
```
verifier sub-agent가 ai.loop.yaml의 verify 단계에서 호출한다.
```

- [ ] **Step 5: `eval/thresholds.yaml`의 주석을 바꾼다**

old_string:
```
# verifier가 이 기준을 넘지 못하면 rag.loop.yaml의 verify를 실패시킨다.
```
new_string:
```
# verifier가 이 기준을 넘지 못하면 ai.loop.yaml의 verify를 실패시킨다.
```

- [ ] **Step 6: `plans/sprint-01.md`를 바꾼다**

old_string:
```
- `loops/rag.loop.yaml`의 verify.gates(retrieval@k/faithfulness/answer_relevancy)를 전부 통과하는
```
new_string:
```
- `loops/ai.loop.yaml`의 verify.gates(retrieval@k/faithfulness/answer_relevancy — 이 SRM
  인스턴스는 FAQ RAG이므로 이 세 지표를 실제 값으로 채운다)를 전부 통과하는
```

- [ ] **Step 7: `plans/task-001.md`를 바꾼다 (4곳)**

old_string:
```
- 실행 loop: loops/rag.loop.yaml
- 상태: todo
- worker: rag-worker (permissions.policy.md 범위 내: `ai/`, `ai/prompts/` 쓰기)
```
new_string:
```
- 실행 loop: loops/ai.loop.yaml
- 상태: todo
- worker: ai-worker (permissions.policy.md 범위 내: `ai/`, `ai/prompts/` 쓰기)
```

old_string:
```
- 건드리는 경로: `ai/`, `ai/prompts/` (rag-worker 쓰기 권한 범위)
```
new_string:
```
- 건드리는 경로: `ai/`, `ai/prompts/` (ai-worker 쓰기 권한 범위)
```

old_string:
```
- `loops/rag.loop.yaml`의 verify.gates 전부 통과: retrieval@k ≥ 0.80, faithfulness ≥ 0.85,
```
new_string:
```
- `loops/ai.loop.yaml`의 verify.gates 전부 통과: retrieval@k ≥ 0.80, faithfulness ≥ 0.85,
```

old_string:
```
- self-eval 없음: rag-worker는 eval을 스스로 돌려 통과 판정하지 않는다(verifier가 판정)
```
new_string:
```
- self-eval 없음: ai-worker는 eval을 스스로 돌려 통과 판정하지 않는다(verifier가 판정)
```

old_string:
```
- 임베딩 모델·청크 전략·Top-K·retriever 변경은 ADR 필수(rag-worker.spec.md 결정 규약).
```
new_string:
```
- 임베딩 모델·청크 전략·Top-K·retriever 변경은 ADR 필수(ai-worker.spec.md 결정 규약).
```

- [ ] **Step 8: `plans/task-index.md`를 바꾼다**

old_string:
```
| [T-001](task-001.md) | sprint-01 | ai | loops/rag.loop.yaml | todo | - | docs/traceability.md#T-001 |
```
new_string:
```
| [T-001](task-001.md) | sprint-01 | ai | loops/ai.loop.yaml | todo | - | docs/traceability.md#T-001 |
```

- [ ] **Step 9: `docs/decisions/ADR-006-import-navendor-prd-frd-and-real-api.md`를 바꾼다 (3곳)**

old_string:
```
  `eval/thresholds.yaml`, `loops/rag.loop.yaml`, `agent-specs/rag-worker.spec.md`
```
new_string:
```
  `eval/thresholds.yaml`, `loops/ai.loop.yaml`, `agent-specs/ai-worker.spec.md`
```

old_string:
```
  늘리는 것은 곧 통제 범위를 늘리는 것")에 따라 `rag-worker`만 접근하도록 권한을 좁혀 유지한다
  (`harness/permissions.policy.md`는 이미 `ai/`, `ai/prompts/`로 rag-worker 쓰기 범위를 한정).
```
new_string:
```
  늘리는 것은 곧 통제 범위를 늘리는 것")에 따라 `ai-worker`만 접근하도록 권한을 좁혀 유지한다
  (`harness/permissions.policy.md`는 이미 `ai/`, `ai/prompts/`로 ai-worker 쓰기 범위를 한정).
```

old_string:
```
  `rag-worker`의 프롬프트/파이프라인 구현 시 실제 API 키 주입 경로(환경변수/시크릿 매니저)를
```
new_string:
```
  `ai-worker`의 프롬프트/파이프라인 구현 시 실제 API 키 주입 경로(환경변수/시크릿 매니저)를
```

- [ ] **Step 10: `docs/decisions/ADR-007-faq-fallback-when-no-evidence.md`를 바꾼다 (3곳)**

old_string:
```
  `plans/task-001.md`, `agent-specs/rag-worker.spec.md`
```
new_string:
```
  `plans/task-001.md`, `agent-specs/ai-worker.spec.md`
```

old_string:
```
이 결정은 rag-worker가 임의로 확정하지 않고 이 ADR로 발의해 사람 확인을 기다린다. 다만 AI 워크스트림
```
new_string:
```
이 결정은 ai-worker가 임의로 확정하지 않고 이 ADR로 발의해 사람 확인을 기다린다. 다만 AI 워크스트림
```

old_string:
```
자체는 건드리지 않되(임포트 스냅샷, 손편집 금지) 이 ADR을 정본으로 `agent-specs/rag-worker.spec.md`
/ `ai/prompts/`에 반영한다. Human PM이 다른 안(A/C 등)을 원하면 이 ADR을 갱신하고 rag-worker 구현도
```
new_string:
```
자체는 건드리지 않되(임포트 스냅샷, 손편집 금지) 이 ADR을 정본으로 `agent-specs/ai-worker.spec.md`
/ `ai/prompts/`에 반영한다. Human PM이 다른 안(A/C 등)을 원하면 이 ADR을 갱신하고 ai-worker 구현도
```

- [ ] **Step 11: 전체 리네임 완결성 확인**

```bash
cd "C:\dev\agent-harness"
grep -ril "rag-worker\|rag\.loop\|loops/rag" --include="*.md" --include="*.yaml" --include="*.py" . \
  | grep -v "docs/agent-control-log.md" \
  | grep -v "docs/agent-control-journal.md" \
  | grep -v "docs/decisions/ADR-005" \
  | grep -v "docs/harness-log.md" \
  | grep -v "docs/superpowers/specs/2026-07-17-generic-harness-intake-design.md"
```
Expected: 아무 결과 없음 — 남아있다면 역사 기록(제외 목록) 이외의 곳에 놓친 참조가 있다는 뜻이므로
찾아서 고친다.

- [ ] **Step 12: `docs/harness-log.md`에 이번 리네임 작업을 기록한다**

파일 끝에 추가:

```markdown

## [2026-07-17] harness · rag-to-ai-rename · goal_loop
- action: `rag-worker`/`loops/rag.loop.yaml`을 `ai-worker`/`loops/ai.loop.yaml`로 리네임하고
  일반화(agent-specs, loops, permissions.policy.md, hook POLICY 미러, generate_agents.py
  TOOLS_MAP, AGENTS.md, orchestrator.spec.md, HANDOFF.md, ai/README.md 등 전체 참조 갱신).
  `docs/superpowers/specs/2026-07-17-generic-harness-intake-design.md` 컴포넌트 A 실행.
- verify: hook 시나리오 2건(ai-worker의 backend/ 쓰기 차단, ai/prompts/ 쓰기 허용) 기대대로 동작.
  `generate_agents.py --check` 최신 확인. 전체 grep으로 rag-worker/rag.loop 잔존 참조 0건(역사
  기록 제외) 확인.
- record: PR 없음(로컬 커밋 3건), ADR 없음(가역적 리네임)
- 다음 루프에 넘길 컨텍스트: `.claude/commands/intake.md` 신설이 남음(같은 설계 문서 컴포넌트 B).
```

- [ ] **Step 13: 커밋**

```bash
cd "C:\dev\agent-harness"
git add -A
git commit -m "$(cat <<'EOF'
Update remaining docs/plans references from rag-worker to ai-worker

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: `.claude/commands/intake.md` 신설

**Files:**
- Create: `.claude/commands/intake.md`

- [ ] **Step 1: 디렉터리 확인**

```bash
cd "C:\dev\agent-harness"
ls .claude/commands 2>&1 || echo "no dir yet"
```

- [ ] **Step 2: 커맨드 파일을 작성한다**

`.claude/commands/intake.md`를 다음 내용으로 생성한다:

```markdown
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
```

- [ ] **Step 3: frontmatter가 유효한 YAML인지 확인한다**

```bash
cd "C:\dev\agent-harness"
python3 -c "
import re, yaml
text = open('.claude/commands/intake.md', encoding='utf-8').read()
m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
assert m, 'frontmatter not found'
meta = yaml.safe_load(m.group(1))
print(meta)
assert 'description' in meta
"
```
Expected: `{'description': 'requirements/의 프로젝트 문서를 읽어...'}` 출력, 에러 없음.

- [ ] **Step 4: 커밋**

```bash
git add .claude/commands/intake.md
git commit -m "$(cat <<'EOF'
Add /intake slash command for generic requirements-doc bootstrap

Implements docs/superpowers/specs/2026-07-17-generic-harness-intake-design.md
component B: reading requirements/, domain tagging, two escalation gates
(external-implementation signal, connector/cost signal), auto-drafting
ADR-proposed stubs for open questions, and a planned Sprint-01 candidate.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: 검증 1 — 기존 SRM 문서로 멱등성 확인 (회귀 없음)

**Files:** (읽기만, 쓰기 없어야 함)

- [ ] **Step 1: 재실행 전 상태를 기록해둔다**

```bash
cd "C:\dev\agent-harness"
git rev-parse HEAD
git status --short
```
Expected: `git status --short`가 비어 있다(깨끗한 상태).

- [ ] **Step 2: `/intake` 절차를 `requirements/prd.md`, `requirements/frd.md`(이미 처리된 SRM
문서)에 대해 `.claude/commands/intake.md`의 1~11단계 그대로 따라 수동으로 재실행한다.**

이 단계는 실제로 Claude Code 세션에서 `/intake`를 입력해 실행한다(또는 이 계획을 실행하는
에이전트가 `.claude/commands/intake.md`의 절차를 그대로 따라 직접 수행한다).

- [ ] **Step 3: 결과를 확인한다**

```bash
git status --short
```
Expected: **아무 변경도 없어야 한다** (`docs/traceability.md`의 FR-017 행 중복 생성 없음,
`plans/sprint-01.md` 재생성 시도 없이 "이미 sprint-01이 존재합니다" 보고로 대체됨,
`docs/decisions/`에 OQ-006~015 중복 ADR 생성 없음 — 단, 아직 ADR로 안 만들어진 OQ가 있다면
그건 정상적인 신규 생성이므로 그 경우는 diff가 있을 수 있다. 이 케이스에서는 새로 생긴 파일이
`docs/decisions/adr-index.md`와 정확히 일치하는지, 그리고 이미 있는 OQ-006/OQ-010(ADR-006/007로
이미 커버됨)에 대해서는 중복이 없는지를 직접 확인한다).

- [ ] **Step 4: 결과를 harness-log에 기록한다**

`docs/harness-log.md`에 검증 결과를 추가하고 커밋한다(Task 4 Step 12와 같은 형식).

---

### Task 7: 검증 2 — 이종 프로젝트(AI 없음) 드라이런

**Files:** (임시 브랜치에서만 작업, 최종적으로 버림)

- [ ] **Step 1: 드라이런용 임시 브랜치를 만든다**

```bash
cd "C:\dev\agent-harness"
git checkout -b test/intake-dry-run-no-ai
```

- [ ] **Step 2: 기존 `requirements/`를 치우고 가상의 미니 PRD로 교체한다**

```bash
mkdir -p /tmp/req-backup
mv requirements/*.md /tmp/req-backup/
```

`requirements/todo-app-prd.md`를 다음 내용으로 만든다(AI 도메인 언급이 전혀 없는 미니 PRD):

```markdown
# TODO 앱 PRD

## 요구사항

| ID | 설명 | 우선순위 |
|----|------|----------|
| REQ-001 | 사용자는 할 일을 추가할 수 있다 (백엔드 API로 저장) | 필수 |
| REQ-002 | 사용자는 할 일 목록 화면에서 완료 여부를 체크할 수 있다 | 필수 |
| REQ-003 | 사용자는 할 일을 삭제할 수 있다 | 필수 |

## Interface Expectations

### Backend
- REQ-001, REQ-003: 할 일 CRUD API

### Frontend
- REQ-002: 할 일 목록 화면, 체크박스 UI
```

- [ ] **Step 3: `.claude/commands/intake.md` 절차를 이 문서에 대해 수동 실행한다**

- [ ] **Step 4: 결과 확인**

```bash
ls loops/ | grep -i ai
```
Expected: **아무 결과 없음** — AI 도메인이 문서에 없으므로 `loops/ai.loop.yaml`이 새로 만들어지지
않아야 한다(기존 `loops/ai.loop.yaml`은 이미 있으므로 삭제 대상은 아니지만, 이 드라이런은 애초에
없는 상태에서 시작했어야 정확하다 — 실제로는 `loops/backend.loop.yaml`, `loops/frontend.loop.yaml`
만 참조되고 `ai/` 관련 신규 파일이 하나도 생기지 않는지를 확인한다).

```bash
cat docs/traceability.md | grep -c "REQ-00[123]"
```
Expected: `3` (세 요구사항 모두 골격 행으로 추가됨).

- [ ] **Step 5: 드라이런 정리 — 브랜치를 버리고 원상복구한다**

```bash
cd "C:\dev\agent-harness"
git checkout master
git branch -D test/intake-dry-run-no-ai
mv /tmp/req-backup/*.md requirements/
git status --short
```
Expected: `git status --short`가 비어 있다(master가 그대로 복원됨).

---

### Task 8: 검증 3 — 게이트 1(외부 구현 존재 신호) 발동 확인

**Files:** (임시 브랜치에서만 작업, 최종적으로 버림)

- [ ] **Step 1: 드라이런용 임시 브랜치를 만든다**

```bash
cd "C:\dev\agent-harness"
git checkout -b test/intake-dry-run-gate1
mkdir -p /tmp/req-backup2
mv requirements/*.md /tmp/req-backup2/
```

- [ ] **Step 2: "이미 구현됨" 신호가 있는 가상 문서를 만든다**

`requirements/other-project-prd.md`:

```markdown
# 가상 프로젝트 PRD

## 요구사항

| ID | 설명 | 우선순위 |
|----|------|----------|
| REQ-001 | 사용자는 로그인할 수 있다 | 필수 |

## 참고
이 기능은 `C:\dev\other-project\backend\auth\`에 이미 구현 완료되었으며, PR #12에서 병합됨.
```

- [ ] **Step 3: `.claude/commands/intake.md` 4단계까지 수동 실행하고 확인**

Expected: 4단계에서 "절대 경로/PR 번호/'구현 완료' 문구" 신호(`C:\dev\other-project\...`,
`PR #12`, "이미 구현 완료")를 감지해 AskUserQuestion으로 사람에게 확인을 요청하며 5단계 이후로
**진행하지 않아야 한다**. `git status --short`가 비어 있어야 한다(게이트에서 멈췄으므로 아직
아무 파일도 안 씀).

- [ ] **Step 4: 드라이런 정리**

```bash
cd "C:\dev\agent-harness"
git checkout master
git branch -D test/intake-dry-run-gate1
mv /tmp/req-backup2/*.md requirements/
git status --short
```
Expected: 비어 있음(복원 확인).

---

### Task 9: 마무리 — `docs/project-state.md` 갱신 + push

**Files:**
- Modify: `docs/project-state.md`

- [ ] **Step 1: `docs/project-state.md`의 "남은 큰 일"에 완료 표시를 추가한다**

old_string:
```
- [ ] 첫 Sprint→Task→loop→verify→record 1회전 실증 (FR-017 후보)
```
new_string:
```
- [x] 첫 Sprint→Task→loop→verify→record 1회전 실증 (FR-017 후보) — Sprint-01 정의 완료, 실제
  구현(T-001)은 아직 미착수
- [x] `rag-worker` → `ai-worker` 일반화 + `/intake` 부트스트랩 커맨드 신설
  (`docs/superpowers/specs/2026-07-17-generic-harness-intake-design.md`)
```

- [ ] **Step 2: 커밋 및 push**

```bash
cd "C:\dev\agent-harness"
git add docs/project-state.md
git commit -m "$(cat <<'EOF'
Update project-state.md after generic /intake bootstrap work

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
git push origin master
```
Expected: push 성공, `https://github.com/gyujin00/agent-harness`에 반영됨.

---

## Self-Review 체크리스트 (계획 작성자용, 실행 전 확인됨)

- **스펙 커버리지**: 설계 문서의 컴포넌트 A(리네임) → Task 1~4, 컴포넌트 B(intake 커맨드) →
  Task 5, 테스트/검증 계획의 3개 시나리오 → Task 6~8. 전부 대응 확인.
- **플레이스홀더 스캔**: "TODO"/"TBD" 없음 — 모든 Step에 실행 가능한 정확한 명령/전체 파일
  내용을 넣었음.
- **이름 일관성**: `ai-worker`/`loops/ai.loop.yaml`/`agent-specs/ai-worker.spec.md` 표기가
  Task 1~5 전체에서 동일함(중간에 `ai_worker`나 `AI-worker` 같은 변형 없음).
