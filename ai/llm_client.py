"""ai/llm_client.py — shared OpenAI client bootstrap + prompt-section loader.

Factored out of ai/embeddings.py, ai/generation.py, ai/scoring.py (T-001 code
review, Important #2): all three needed the identical "get a real OpenAI
client from OPENAI_API_KEY, no mock fallback" bootstrap, and generation.py /
scoring.py both needed to pull a named "## Section" out of an
ai/prompts/*.md file. Centralizing both here means the next AI feature that
lands in ai/ (FR-016/018/019/020) reuses this instead of adding a 4th/5th
copy-pasted version.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

_client = None


def get_client():
    """Return a shared OpenAI client, built from OPENAI_API_KEY.

    Real API only (docs/decisions/ADR-006) — deliberately does not fall back
    to a mock when the key is missing; callers should see a clear error
    instead of a silently-wrong offline mode.
    """
    global _client
    if _client is None:
        from openai import OpenAI

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set in the environment. "
                "This module calls the real OpenAI API (docs/decisions/ADR-006) and does not fall back to a mock."
            )
        _client = OpenAI(api_key=api_key)
    return _client


def load_prompt_section(path: Path, section: str) -> str:
    """Extract the body of a '## {section}' markdown section out of a
    prompt file in ai/prompts/, up to the next '## ' heading (or EOF).

    Keeps prompt text living in one place (the .md file, reviewable/diffable
    independent of code) instead of duplicated into Python string literals.
    Used for both '## System Prompt' and, if a caller ever needs it,
    '## User Prompt' sections across ai/prompts/*.md.
    """
    raw = Path(path).read_text(encoding="utf-8")
    pattern = rf"## {re.escape(section)}\s*\n\n(.*?)(?:\n\n## |\Z)"
    m = re.search(pattern, raw, re.DOTALL)
    if not m:
        raise RuntimeError(f"could not find '## {section}' section in {path}")
    return m.group(1).strip()
