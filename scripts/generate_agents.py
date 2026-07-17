#!/usr/bin/env python3
"""scripts/generate_agents.py — agent-specs/*.spec.md -> .claude/agents/*.md 생성기

단일 원본(agent-specs/*.spec.md)에서 파생 산출물(.claude/agents/*.md)을 만든다.
AGENTS.md 규칙: ".claude/agents/*"는 손편집 금지, 이 스크립트로만 재생성한다.

사용법:
    python3 scripts/generate_agents.py            # 전체 재생성
    python3 scripts/generate_agents.py --check     # 산출물이 최신인지만 검사 (CI용, 쓰기 없음)

각 spec.md 구조:
    ---
    name: <agent 이름>
    role: <한 줄 역할 설명>
    generates: .claude/agents/<name>.md
    loop: loops/<domain>.loop.yaml   (선택)
    ---
    # 본문 (책임/권한/절차/금지/record 등, Claude Code subagent의 system prompt로 그대로 사용)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml  # pip install pyyaml

ROOT = Path(__file__).resolve().parent.parent
SPEC_DIR = ROOT / "agent-specs"

# Claude Code 'tools' 필드는 도구 종류만 제한한다 (경로 단위 제한 아님).
# 경로/명령 단위 강제는 harness/permissions.policy.md + .claude/hooks/ (다음 작업 2번)가 담당한다.
# 아래 매핑은 agent-specs/*.spec.md의 "권한" 절과 일관되게 유지할 것.
TOOLS_MAP: dict[str, list[str]] = {
    "orchestrator": ["Read", "Grep", "Glob", "Bash", "Task"],
    "backend-worker": ["Read", "Write", "Edit", "Bash", "Grep", "Glob"],
    "frontend-worker": ["Read", "Write", "Edit", "Bash", "Grep", "Glob"],
    "rag-worker": ["Read", "Write", "Edit", "Bash", "Grep", "Glob"],
    "verifier": ["Read", "Grep", "Glob", "Bash", "Write"],
}

GENERATED_HEADER = """<!-- AUTO-GENERATED — 손편집 금지.
     원본: {source}
     재생성: python3 scripts/generate_agents.py
-->
"""


def split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        raise ValueError("frontmatter(---)가 없습니다")
    _, fm, body = text.split("---", 2)
    meta = yaml.safe_load(fm) or {}
    return meta, body.lstrip("\n")


def render_agent_md(meta: dict, body: str, source: Path) -> str:
    name = meta["name"]
    role = meta.get("role", "").strip()
    tools = TOOLS_MAP.get(name)
    if tools is None:
        raise ValueError(f"TOOLS_MAP에 '{name}' 항목이 없습니다 — scripts/generate_agents.py에 추가하세요")

    frontmatter = (
        "---\n"
        f"name: {name}\n"
        f"description: {role}\n"
        f"tools: {', '.join(tools)}\n"
        "---\n"
    )
    return GENERATED_HEADER.format(source=source.relative_to(ROOT).as_posix()) + frontmatter + "\n" + body.rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="쓰지 않고 최신 상태인지만 검사 (CI용)")
    args = parser.parse_args()

    specs = sorted(SPEC_DIR.glob("*.spec.md"))
    if not specs:
        print(f"agent-specs에서 *.spec.md를 찾지 못했습니다: {SPEC_DIR}", file=sys.stderr)
        return 1

    stale: list[str] = []
    for spec_path in specs:
        meta, body = split_frontmatter(spec_path.read_text(encoding="utf-8"))
        generates = meta.get("generates")
        if not generates:
            print(f"[SKIP] {spec_path.name}: 'generates' 필드 없음", file=sys.stderr)
            continue

        out_path = ROOT / generates
        rendered = render_agent_md(meta, body, spec_path)

        if args.check:
            current = out_path.read_text(encoding="utf-8") if out_path.exists() else None
            if current != rendered:
                stale.append(str(out_path.relative_to(ROOT)))
            continue

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
        print(f"[OK] {spec_path.relative_to(ROOT)} -> {out_path.relative_to(ROOT)}")

    if args.check:
        if stale:
            print("STALE (재생성 필요): " + ", ".join(stale))
            return 1
        print("모든 .claude/agents/*.md가 최신 상태입니다.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
