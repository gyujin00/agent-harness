#!/usr/bin/env python3
""".claude/hooks/enforce_permissions.py — PreToolUse hook: harness/permissions.policy.md 강제

harness/permissions.policy.md(단일 원본)의 경로/명령 권한 표를 코드화한 것이다.
정책 문서를 바꾸면 아래 POLICY/패턴도 함께 갱신할 것 (v1은 자동 파싱하지 않고 손으로 미러링한다.
agent-specs -> .claude/agents 처럼 이 파일도 언젠가 정책 문서에서 자동 생성하도록 승격할 수 있다).

동작 요약
  1) agent_type이 없는 호출(메인 세션 = 사람이 AGENTS.md/harness/agent-specs/loops/eval을
     직접 편집하는 컨텍스트)은 경로 제한을 적용하지 않는다. 다만 공통 파괴적 명령은 막는다.
  2) agent_type이 POLICY에 있는 5개 harness agent 중 하나면 그 agent의 경로/명령 정책을 강제한다.
  3) 그 외(POLICY에 없는 낯선 subagent, 예: Explore/general-purpose)는 이 하네스 관할 밖으로 보고
     통과시킨다 (공통 파괴적 명령 차단은 여전히 적용).
  4) 차단 시 docs/agent-control-log.md에 BLOCK 이벤트를 남긴다
     (harness/permissions.policy.md "위반 처리" 1~2단계). 3단계(orchestrator 재위임)는
     차단 사유 메시지로 해당 agent에게 유도한다 — hook은 다른 agent를 직접 호출할 수 없다.

알려진 한계 (v1, 다음에 다듬을 것)
  - Bash 명령 필터는 문자열/정규식 매칭이라 변수 조립 등으로 우회 가능하다.
  - Grep/Glob은 path 인자가 없으면(=repo 전체 대상) 강제하지 않는다.
  - 정책은 harness/permissions.policy.md에서 자동 파싱하지 않고 손으로 미러링한다(드리프트 주의).
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

# ── harness/permissions.policy.md "경로 권한" 표 미러 ──────────────────────
# write_allow: Write/Edit 허용 경로 접두어. 빈 리스트면 그 tool을 전면 차단.
# read_allow:  Read/Grep/Glob 허용 경로 접두어. "*"면 전체 허용.
POLICY: dict[str, dict[str, list[str]]] = {
    "orchestrator": {
        "write_allow": ["plans/", "docs/agent-control-log.md"],
        "read_allow": ["*"],
    },
    "backend-worker": {
        "write_allow": ["backend/", "openapi.yaml"],
        "read_allow": ["backend/", "plans/", "loops/", "docs/"],
    },
    "frontend-worker": {
        "write_allow": ["frontend/"],
        "read_allow": ["frontend/", "openapi.yaml", "plans/", "docs/"],
    },
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

# ── harness/permissions.policy.md "명령 권한" 미러 ─────────────────────────
DESTRUCTIVE_PATTERNS = [  # 전 Agent 공통 차단 (메인 세션 포함)
    r"\brm\s+-rf\b",
    r"\bgit\s+push\b[^\n]*(--force\b|-f\b|--force-with-lease\b)",
    r"\bgit\s+reset\s+--hard\b[^\n]*&&[^\n]*\bpush\b",
    r"\bcat\s+[^\n]*\.env\b",
    r"\bprintenv\b",
]

DEPLOY_PATTERNS = [  # worker + verifier 차단 (배포/릴리스)
    r"\bgit\s+push\b",
    r"\bnpm\s+publish\b",
    r"\bgh\s+release\b",
    r"\bvercel\b[^\n]*--prod\b",
    r"\bnetlify\s+deploy\b[^\n]*--prod\b",
    r"\bkubectl\s+apply\b",
    r"\bterraform\s+apply\b",
    r"\bdocker\s+push\b",
]

VERIFIER_EXTRA_PATTERNS = [  # verifier는 "읽기 전용 검증 명령 + eval 실행만" 허용
    r"\bgit\s+commit\b",
    r"\bgit\s+add\b",
    r"\bsed\s+-i\b",
]

REPO_ROOT_MARKERS = ("AGENTS.md", ".git")
AGENT_CONTROL_LOG = "docs/agent-control-log.md"


def find_repo_root(cwd: Path) -> Path:
    cur = cwd
    for _ in range(6):
        if any((cur / m).exists() for m in REPO_ROOT_MARKERS):
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return cwd


def to_rel_posix(root: Path, abs_path: str) -> str | None:
    if not abs_path:
        return None
    try:
        return Path(abs_path).resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return None


def path_allowed(rel_path: str, allow_prefixes: list[str]) -> bool:
    if "*" in allow_prefixes:
        return True
    return any(rel_path == pfx.rstrip("/") or rel_path.startswith(pfx) for pfx in allow_prefixes)


def log_block(root: Path, agent: str, detail: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"[{ts}] BLOCK · {agent} · {detail}\n"
    try:
        with (root / AGENT_CONTROL_LOG).open("a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass  # 기록 실패로 hook 자체를 죽이지 않는다


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


def allow() -> None:
    sys.exit(0)


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except Exception:
        allow()
        return

    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input") or {}
    agent = event.get("agent_type")  # None = 메인 세션 (사람이 직접 다루는 컨텍스트)
    cwd = Path(event.get("cwd") or ".")
    root = find_repo_root(cwd)

    # 1) 공통 파괴적 명령 — 전 Agent(메인 세션 포함) 차단
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        for pat in DESTRUCTIVE_PATTERNS:
            if re.search(pat, command):
                log_block(root, agent or "main", f"destructive command blocked: {command!r}")
                deny(f"파괴적 명령 차단(permissions.policy.md 공통 규칙): {command!r}")

    # agent_type이 없으면 메인 세션 — 도메인별 경로 제한은 적용하지 않는다.
    if not agent:
        allow()
        return

    # 2) worker/verifier 배포·릴리스 명령 차단, verifier 전용 추가 차단
    if tool_name == "Bash" and agent in (WORKER_NAMES | {"verifier"}):
        command = tool_input.get("command", "")
        for pat in DEPLOY_PATTERNS:
            if re.search(pat, command):
                log_block(root, agent, f"deploy/release command blocked: {command!r}")
                deny(f"'{agent}'는 배포/릴리스 명령을 실행할 수 없습니다: {command!r}")
        if agent == "verifier":
            for pat in VERIFIER_EXTRA_PATTERNS:
                if re.search(pat, command):
                    log_block(root, agent, f"verifier write-ish command blocked: {command!r}")
                    deny(f"verifier는 읽기 전용 검증 + eval 실행만 허용됩니다: {command!r}")

    policy = POLICY.get(agent)
    if policy is None:
        allow()  # 이 5개 harness agent가 아니면 관할 밖 — 통과
        return

    # 3) 경로 기반 쓰기/읽기 제한
    if tool_name in ("Write", "Edit"):
        rel = to_rel_posix(root, tool_input.get("file_path", ""))
        if rel is not None and not path_allowed(rel, policy["write_allow"]):
            log_block(root, agent, f"write outside allowed scope: {rel}")
            deny(
                f"'{agent}'는 '{rel}'에 쓸 수 없습니다 "
                f"(permissions.policy.md 허용 범위: {policy['write_allow'] or '없음'}). "
                "orchestrator에게 재위임하세요."
            )

    elif tool_name in ("Read", "Grep", "Glob"):
        rel = to_rel_posix(root, tool_input.get("file_path") or tool_input.get("path") or "")
        if rel is not None and not path_allowed(rel, policy["read_allow"]):
            log_block(root, agent, f"read outside allowed scope: {rel}")
            deny(
                f"'{agent}'는 '{rel}'을 읽을 수 없습니다 "
                f"(permissions.policy.md 허용 범위: {policy['read_allow']})."
            )

    allow()


if __name__ == "__main__":
    main()
