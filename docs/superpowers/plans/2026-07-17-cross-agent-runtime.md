# Cross-Agent Harness Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a provider-neutral Python runtime that executes one Task Contract through isolated work, independent verification, bounded retry, evidence recording, and optional Draft PR creation with either Claude Code or Codex.

**Architecture:** `harness_runtime` owns contracts, state, policy, recording, and the loop. Thin provider adapters translate the same `AgentRequest` into `claude -p` or `codex exec`; a fake provider proves the full loop without model cost. Existing `AGENTS.md`, `agent-specs/`, `loops/`, `harness/`, and `eval/` remain the control-plane sources of truth.

**Tech Stack:** Python 3.11+, dataclasses, pathlib, subprocess, PyYAML 6+, pytest 8+, Git CLI, GitHub CLI.

## Global Constraints

- `AGENTS.md` remains the single constitutional source; `CLAUDE.md` only imports it.
- Worker and verifier must be separate provider invocations and sessions.
- Evaluators, policies, Task Contracts, and merge authority are locked.
- Runtime may create a Draft PR but exposes no merge or deploy operation.
- Runtime uses subprocess argument arrays and never dangerous permission-bypass flags.
- Raw transcripts stay under ignored `.harness/runs/`; sanitized evidence goes under `docs/runs/`.
- First release supports a single `human.goal` Task loop; scheduled and parallel Ops loops remain out of scope.

---

### Task 1: Package, Task Contract, and Schemas

**Files:**
- Create: `pyproject.toml`
- Create: `harness_runtime/__init__.py`
- Create: `harness_runtime/contracts.py`
- Create: `harness/schemas/task-contract.schema.json`
- Create: `harness/schemas/agent-result.schema.json`
- Create: `harness/schemas/verifier-report.schema.json`
- Modify: `plans/_task.template.md`
- Test: `tests/test_contracts.py`

**Interfaces:**
- Produces: `TaskContract`, `PullRequestPolicy`, `ContractError`, and `load_task_contract(path: Path, root: Path) -> TaskContract`.
- `TaskContract` exposes `id`, `domain`, `loop`, `worker`, `status`, `max_attempts`, `timeout_minutes`, `editable_paths`, `locked_paths`, `verification_commands`, `pr`, `path`, and `body`.

- [ ] **Step 1: Write failing contract tests**

```python
def test_loads_valid_task_contract(tmp_path: Path) -> None:
    task = write_task(tmp_path, VALID_TASK)
    contract = load_task_contract(task, tmp_path)
    assert contract.id == "T-002"
    assert contract.pr.draft is True

def test_rejects_task_without_frontmatter(tmp_path: Path) -> None:
    task = write_task(tmp_path, "# Task only")
    with pytest.raises(ContractError, match="YAML frontmatter"):
        load_task_contract(task, tmp_path)

def test_rejects_locked_editable_overlap(tmp_path: Path) -> None:
    task = write_task(tmp_path, VALID_TASK.replace("locked_paths: [eval/]", "locked_paths: [backend/]"))
    with pytest.raises(ContractError, match="overlap"):
        load_task_contract(task, tmp_path)
```

- [ ] **Step 2: Run the tests and confirm RED**

Run: `python -m pytest tests/test_contracts.py -q`

Expected: collection fails because `harness_runtime.contracts` does not exist.

- [ ] **Step 3: Implement the immutable contract model and frontmatter parser**

```python
@dataclass(frozen=True)
class PullRequestPolicy:
    enabled: bool = False
    draft: bool = True

@dataclass(frozen=True)
class TaskContract:
    id: str
    domain: str
    loop: Path
    status: str
    worker: str
    max_attempts: int
    timeout_minutes: int
    editable_paths: tuple[str, ...]
    locked_paths: tuple[str, ...]
    verification_commands: tuple[str, ...]
    pr: PullRequestPolicy
    path: Path
    body: str

def load_task_contract(path: Path, root: Path) -> TaskContract:
    text = path.read_text(encoding="utf-8")
    frontmatter, body = _split_frontmatter(text)
    data = yaml.safe_load(frontmatter)
    _validate_required_fields(data)
    contract = _to_contract(data, body, path, root)
    _validate_paths(contract, root)
    return contract
```

- [ ] **Step 4: Add JSON schemas and frontmatter to `_task.template.md`**

The template must contain exact defaults: `status: todo`, `max_attempts: 3`, `timeout_minutes: 30`,
`editable_paths`, `locked_paths: [eval/, harness/, plans/]`, `verification_commands`, and Draft PR policy.

- [ ] **Step 5: Run contract tests and the full suite**

Run: `python -m pytest tests/test_contracts.py -q`

Expected: all contract tests pass.

- [ ] **Step 6: Commit**

```powershell
git add pyproject.toml harness_runtime harness/schemas plans/_task.template.md tests/test_contracts.py
git commit -m "feat: add machine-readable task contracts"
```

---

### Task 2: State Machine and Durable Recorder

**Files:**
- Create: `harness_runtime/state.py`
- Create: `harness_runtime/recorder.py`
- Test: `tests/test_state.py`
- Test: `tests/test_recorder.py`

**Interfaces:**
- Produces: `RunStatus`, `RunEvent`, `InvalidTransition`, `next_status(current, requested)`, and `RunRecorder`.
- `RunRecorder.append(status, actor, detail, evidence=())` writes matching local and sanitized JSONL events and can recover the last status.

- [ ] **Step 1: Write failing transition and recovery tests**

```python
def test_fail_can_return_to_action() -> None:
    assert next_status(RunStatus.IN_VERIFY, RunStatus.BACK_TO_ACTION) is RunStatus.BACK_TO_ACTION
    assert next_status(RunStatus.BACK_TO_ACTION, RunStatus.IN_PROGRESS) is RunStatus.IN_PROGRESS

def test_pr_ready_cannot_transition_to_merge() -> None:
    with pytest.raises(InvalidTransition):
        next_status(RunStatus.PR_READY, "merged")

def test_recorder_recovers_last_complete_event(tmp_path: Path) -> None:
    recorder = RunRecorder(tmp_path, tmp_path / "docs", "run-1")
    recorder.append(RunStatus.PREPARING, "orchestrator", "context")
    recorder.append(RunStatus.IN_PROGRESS, "worker", "started")
    assert recorder.last_status() is RunStatus.IN_PROGRESS
```

- [ ] **Step 2: Run tests and confirm RED**

Run: `python -m pytest tests/test_state.py tests/test_recorder.py -q`

Expected: imports fail because state and recorder modules do not exist.

- [ ] **Step 3: Implement explicit allowed transitions**

```python
ALLOWED: dict[RunStatus, frozenset[RunStatus]] = {
    RunStatus.QUEUED: frozenset({RunStatus.PREPARING, RunStatus.INVALID_CONTRACT}),
    RunStatus.PREPARING: frozenset({RunStatus.IN_PROGRESS, RunStatus.BLOCKED}),
    RunStatus.IN_PROGRESS: frozenset({RunStatus.IN_VERIFY, RunStatus.TIMED_OUT, RunStatus.NEEDS_HUMAN}),
    RunStatus.IN_VERIFY: frozenset({RunStatus.BACK_TO_ACTION, RunStatus.RECORDING, RunStatus.NEEDS_HUMAN}),
    RunStatus.BACK_TO_ACTION: frozenset({RunStatus.IN_PROGRESS, RunStatus.NEEDS_HUMAN}),
    RunStatus.RECORDING: frozenset({RunStatus.PR_READY, RunStatus.COMPLETE, RunStatus.NEEDS_HUMAN}),
}
```

- [ ] **Step 4: Implement append-only recording and sanitization**

`RunRecorder` creates `.harness/runs/{run-id}/events.jsonl` and `docs/runs/{run-id}/events.jsonl`, writes
one UTF-8 JSON object per line with UTC timestamp, and replaces values matching `*TOKEN*`, `*KEY*`,
`*SECRET*` environment names with `[REDACTED]`.

- [ ] **Step 5: Run focused and full tests**

Run: `python -m pytest tests/test_state.py tests/test_recorder.py -q`

Expected: all state and recorder tests pass.

- [ ] **Step 6: Commit**

```powershell
git add harness_runtime/state.py harness_runtime/recorder.py tests/test_state.py tests/test_recorder.py
git commit -m "feat: add durable harness run state"
```

---

### Task 3: Context Pack, Locked Surfaces, and Deterministic Gates

**Files:**
- Create: `harness_runtime/context_pack.py`
- Create: `harness_runtime/policy.py`
- Create: `harness_runtime/gates.py`
- Test: `tests/test_context_pack.py`
- Test: `tests/test_policy.py`
- Test: `tests/test_gates.py`

**Interfaces:**
- Produces: `ContextPack`, `build_context_pack(root, contract, feedback=())`, `validate_changed_paths(changed, contract)`, `run_gates(commands, cwd, timeout_seconds)`.
- `GateResult` contains `command`, `exit_code`, `stdout`, `stderr`, `timed_out`, and `passed`.

- [ ] **Step 1: Write failing policy and context tests**

```python
def test_locked_path_change_is_rejected(contract: TaskContract) -> None:
    with pytest.raises(LockedSurfaceViolation, match="eval/thresholds.yaml"):
        validate_changed_paths(["backend/api.py", "eval/thresholds.yaml"], contract)

def test_context_pack_contains_manifest_not_full_repository(root: Path, contract: TaskContract) -> None:
    pack = build_context_pack(root, contract)
    assert contract.path in pack.files
    assert root / "AGENTS.md" in pack.files
    assert root / contract.loop in pack.files
    assert root / "unrelated.txt" not in pack.files
```

- [ ] **Step 2: Write failing gate timeout test**

```python
def test_gate_timeout_is_failure(tmp_path: Path) -> None:
    result = run_gate(
        [sys.executable, "-c", "import time; time.sleep(2)"],
        tmp_path,
        timeout_seconds=1,
    )
    assert result.timed_out is True
    assert result.passed is False
```

- [ ] **Step 3: Run tests and confirm RED**

Run: `python -m pytest tests/test_context_pack.py tests/test_policy.py tests/test_gates.py -q`

Expected: imports fail for the three missing modules.

- [ ] **Step 4: Implement minimal context discovery and locked-surface checks**

Context includes `AGENTS.md`, the Task Contract, selected loop, matching worker spec, verifier spec, harness
policies, explicitly named reference files from the Task body, and structured retry feedback. Paths are resolved
under the repo root and path traversal is rejected.

- [ ] **Step 5: Implement deterministic gate execution**

Use `subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout_seconds, shell=False)`.
Contract command strings are parsed with `shlex.split(..., posix=os.name != "nt")`; shell operators and
redirections are rejected rather than interpreted.

- [ ] **Step 6: Run focused and full tests**

Run: `python -m pytest tests/test_context_pack.py tests/test_policy.py tests/test_gates.py -q`

Expected: all tests pass.

- [ ] **Step 7: Commit**

```powershell
git add harness_runtime/context_pack.py harness_runtime/policy.py harness_runtime/gates.py tests/test_context_pack.py tests/test_policy.py tests/test_gates.py
git commit -m "feat: enforce context and verification boundaries"
```

---

### Task 4: Claude, Codex, and Fake Provider Adapters

**Files:**
- Create: `harness_runtime/providers/__init__.py`
- Create: `harness_runtime/providers/base.py`
- Create: `harness_runtime/providers/claude.py`
- Create: `harness_runtime/providers/codex.py`
- Create: `harness_runtime/providers/fake.py`
- Test: `tests/test_provider_commands.py`
- Test: `tests/test_fake_provider.py`

**Interfaces:**
- Produces: `AgentRole`, `AgentRequest`, `AgentResult`, `ProviderError`, `Provider` protocol, and provider classes.
- `Provider.run(request: AgentRequest) -> AgentResult`.
- `ClaudeProvider.build_command(request)` and `CodexProvider.build_command(request)` return argument tuples.

- [ ] **Step 1: Write failing provider command tests**

```python
def test_claude_worker_uses_structured_noninteractive_mode(request: AgentRequest) -> None:
    command = ClaudeProvider().build_command(request)
    assert command[:2] == ("claude", "-p")
    assert "--json-schema" in command
    assert "--permission-mode" in command
    assert "bypassPermissions" not in command

def test_codex_verifier_is_read_only(verifier_request: AgentRequest) -> None:
    command = CodexProvider().build_command(verifier_request)
    assert command[:2] == ("codex", "exec")
    assert command[command.index("-s") + 1] == "read-only"
    assert "--dangerously-bypass-approvals-and-sandbox" not in command
```

- [ ] **Step 2: Write fake provider sequence test**

```python
def test_fake_provider_returns_scripted_results() -> None:
    provider = FakeProvider([AgentResult.fail("broken"), AgentResult.pass_("fixed")])
    assert provider.run(WORKER_REQUEST).status == "fail"
    assert provider.run(WORKER_REQUEST).status == "pass"
```

- [ ] **Step 3: Run tests and confirm RED**

Run: `python -m pytest tests/test_provider_commands.py tests/test_fake_provider.py -q`

Expected: provider package imports fail.

- [ ] **Step 4: Implement common request/result contracts and subprocess runner**

`AgentResult` accepts only `pass`, `fail`, or `needs_human`. Provider output must validate against the selected
JSON schema; invalid JSON raises `ProviderError` and is never interpreted as success.

- [ ] **Step 5: Implement provider commands**

Claude worker uses `workspace-write` through project permissions; verifier removes edit tools and returns schema
JSON. Codex worker uses `-s workspace-write -a never`; verifier uses `-s read-only -a never`. Both receive prompts
on stdin or a direct non-shell argument and write raw output only to the local run directory.

- [ ] **Step 6: Run focused and full tests**

Run: `python -m pytest tests/test_provider_commands.py tests/test_fake_provider.py -q`

Expected: all provider tests pass.

- [ ] **Step 7: Commit**

```powershell
git add harness_runtime/providers tests/test_provider_commands.py tests/test_fake_provider.py
git commit -m "feat: add Claude and Codex provider adapters"
```

---

### Task 5: Worktree, Loop Runner, and FAIL→Retry→PASS Integration

**Files:**
- Create: `harness_runtime/worktree.py`
- Create: `harness_runtime/orchestrator.py`
- Test: `tests/test_worktree.py`
- Test: `tests/test_fail_retry_pass.py`

**Interfaces:**
- Produces: `WorktreeManager.create(contract, run_id) -> Worktree`, `WorktreeManager.changed_files(worktree)`, and `LoopRunner.run(contract, options) -> RunOutcome`.
- `RunOutcome` contains `run_id`, `status`, `attempts`, `evidence_dir`, and optional `pr_url`.

- [ ] **Step 1: Write failing worktree command test**

```python
def test_worktree_uses_domain_task_branch(contract: TaskContract) -> None:
    manager = WorktreeManager(Path("C:/repo"))
    spec = manager.spec(contract, "20260717-120000")
    assert spec.branch.startswith("backend/T-002-")
    assert ".worktrees" in spec.path.parts
```

- [ ] **Step 2: Write failing loop integration test**

```python
def test_loop_retries_failed_verification_then_records_pass(harness: HarnessFixture) -> None:
    worker = FakeProvider([AgentResult.pass_("attempt-1"), AgentResult.pass_("attempt-2")])
    verifier = FakeProvider([AgentResult.fail("missing contract"), AgentResult.pass_("verified")])
    outcome = harness.runner(worker, verifier).run(harness.contract, create_pr=False)
    assert outcome.status is RunStatus.COMPLETE
    assert outcome.attempts == 2
    assert harness.events.statuses() == [
        "preparing", "in_progress", "in_verify", "back_to_action",
        "in_progress", "in_verify", "recording", "complete",
    ]
```

- [ ] **Step 3: Write retry exhaustion test**

```python
def test_loop_escalates_after_max_attempts(harness: HarnessFixture) -> None:
    verifier = FakeProvider([AgentResult.fail("same defect")] * 3)
    outcome = harness.runner(FakeProvider.passing(), verifier).run(harness.contract, create_pr=False)
    assert outcome.status is RunStatus.NEEDS_HUMAN
    assert outcome.attempts == harness.contract.max_attempts
```

- [ ] **Step 4: Run tests and confirm RED**

Run: `python -m pytest tests/test_worktree.py tests/test_fail_retry_pass.py -q`

Expected: worktree and orchestrator imports fail.

- [ ] **Step 5: Implement the loop in the exact state order**

For each attempt: invoke worker, collect changed files, reject locked changes, run deterministic gates, invoke a
fresh verifier request, record result, and either retry or enter recording. Verifier receives only Task Contract,
diff summary, gate results, and failure checklist. Worker receives only the latest structured feedback on retry.

- [ ] **Step 6: Run integration and full tests**

Run: `python -m pytest tests/test_worktree.py tests/test_fail_retry_pass.py -q`

Expected: PASS for normal, retry, and exhaustion paths.

- [ ] **Step 7: Commit**

```powershell
git add harness_runtime/worktree.py harness_runtime/orchestrator.py tests/test_worktree.py tests/test_fail_retry_pass.py
git commit -m "feat: execute bounded worker verifier loops"
```

---

### Task 6: CLI, Draft PR Boundary, Doctor, and Documentation

**Files:**
- Create: `harness_runtime/__main__.py`
- Create: `harness_runtime/cli.py`
- Create: `harness_runtime/pull_request.py`
- Create: `harness/runtime.yaml`
- Modify: `.gitignore`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `docs/project-state.md`
- Modify: `docs/evaluation/evaluation-map.md`
- Modify: `docs/evaluation/harness-engineering-log.md`
- Modify: `docs/harness-log.md`
- Test: `tests/test_cli.py`
- Test: `tests/test_pull_request.py`
- Test: `tests/test_cross_agent_smoke.py`

**Interfaces:**
- Produces CLI commands `doctor`, `validate TASK`, and `run TASK --worker PROVIDER --verifier PROVIDER [--dry-run] [--create-pr]`.
- `PullRequestManager.create_draft(worktree, title, body) -> str`; no merge method exists.

- [ ] **Step 1: Write failing CLI and PR-boundary tests**

```python
def test_doctor_reports_both_installed_clis(monkeypatch, capsys) -> None:
    monkeypatch.setattr(shutil, "which", lambda name: f"C:/bin/{name}.exe")
    assert main(["doctor"]) == 0
    output = capsys.readouterr().out
    assert "claude" in output and "codex" in output

def test_pull_request_adapter_only_builds_draft_create() -> None:
    command = PullRequestManager().build_create_command("title", "body.md")
    assert command[:3] == ("gh", "pr", "create")
    assert "--draft" in command
    assert "merge" not in command
    assert not hasattr(PullRequestManager, "merge")
```

- [ ] **Step 2: Write cross-provider dry-run test**

```python
@pytest.mark.parametrize(("worker", "verifier"), [("claude", "codex"), ("codex", "claude")])
def test_dry_run_accepts_cross_provider_pairs(project: Path, worker: str, verifier: str) -> None:
    result = run_cli(["run", "plans/task-002.md", "--worker", worker, "--verifier", verifier, "--dry-run"], project)
    assert result.exit_code == 0
    assert f"worker={worker}" in result.stdout
    assert f"verifier={verifier}" in result.stdout
```

- [ ] **Step 3: Run tests and confirm RED**

Run: `python -m pytest tests/test_cli.py tests/test_pull_request.py tests/test_cross_agent_smoke.py -q`

Expected: CLI and pull request modules do not exist.

- [ ] **Step 4: Implement CLI and runtime configuration**

`doctor` checks Python, Git, `claude`, `codex`, and `gh` without model calls. `validate` parses the Task Contract,
loop, role specs, paths, and provider names. `run --dry-run` creates no worktree or model process and prints the
planned state, provider commands with secrets omitted, gates, budget, and PR policy.

- [ ] **Step 5: Implement Draft PR creation only**

The adapter performs `git add`, `git commit`, `git push -u origin <branch>`, and
`gh pr create --draft --title ... --body-file ...`; each command is a subprocess argument list. It contains no
merge/deploy API. Authentication failure returns `needs_human` without deleting the worktree.

- [ ] **Step 6: Update project documentation and audit records**

README adds a 5-minute start section for both providers. AGENTS adds the runtime state machine and explicit
PR-only boundary. `project-state.md`, evaluation map, harness engineering log, and harness log record this
implementation and its verification commands without claiming a real paid model run.

- [ ] **Step 7: Run all verification**

```powershell
python -m pytest -q
python -m compileall -q harness_runtime tests
python -m harness_runtime doctor
python -m harness_runtime validate plans/task-001.md
python -m harness_runtime run plans/task-001.md --worker claude --verifier codex --dry-run
python -m harness_runtime run plans/task-001.md --worker codex --verifier claude --dry-run
git diff --check
```

Expected: tests and compile pass; doctor reports installed tools; validate passes after Task-001 frontmatter
migration; both dry runs show opposite provider pairings; diff check is clean.

- [ ] **Step 8: Commit**

```powershell
git add harness_runtime harness/runtime.yaml .gitignore README.md AGENTS.md plans/task-001.md docs tests pyproject.toml
git commit -m "feat: complete cross-agent harness runtime"
```

---

## Final Verification Checklist

- [ ] Every spec section maps to at least one task above.
- [ ] A case-insensitive placeholder scan over this plan returns no unfinished implementation markers.
- [ ] `python -m pytest -q` passes with zero failures.
- [ ] Provider command tests prove no dangerous bypass flags.
- [ ] Locked-surface tests prove eval/policy/plan mutation is rejected.
- [ ] Fake-provider integration proves `FAIL → back_to_action → PASS → record`.
- [ ] Both Claude/Codex cross-pair dry runs pass without model cost.
- [ ] No runtime merge or deploy method exists.
- [ ] `git diff --check` is clean.
