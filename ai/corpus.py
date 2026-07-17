"""ai/corpus.py — FR-017 FAQ RAG corpus builder.

Builds a deterministic, stable-ID chunk list from the SRM PRD + FRD source
documents (the full documents, not just the FR-017 rows — see
`plans/task-001.md`). Chunking scheme and sizes come from
`eval/thresholds.yaml` (chunk_size=512, chunk_overlap=64) and must not be
changed here without an ADR (see `agent-specs/ai-worker.spec.md`).

Chunk IDs are sequential per source file (e.g. ``prd-0001``, ``frd-0002``)
and are stable across re-runs as long as the source files themselves don't
change — the chunker is a pure function of file content + the two config
constants below, no randomness, no wall-clock input.

The resulting chunk list is cached to ``ai/corpus/chunks.json`` so it's
inspectable (e.g. to pick real ``gold_chunk_ids`` for eval/rag-eval-set.jsonl)
and reusable without re-reading/re-chunking the source docs every run.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = Path(__file__).resolve().parent / "corpus"
CHUNKS_CACHE = CORPUS_DIR / "chunks.json"

# From eval/thresholds.yaml config — do not change without an ADR.
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64

# Source documents (FR-017 / DEP-006 / BR-009: PRD+FRD is the confirmed
# evidence corpus for the FAQ RAG feature).
SOURCE_FILES: dict[str, Path] = {
    "prd": ROOT / "requirements" / "prd.md",
    "frd": ROOT / "requirements" / "frd.md",
}


@dataclass
class Chunk:
    id: str
    source: str
    start: int
    end: int
    text: str


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[tuple[int, int, str]]:
    """Deterministic sliding-window character chunking.

    Returns a list of (start, end, text) spans. Step = chunk_size - overlap.
    The final chunk may be shorter than chunk_size (it's just whatever text
    is left). Pure function of (text, chunk_size, overlap) — same input
    always yields the same spans, which is what makes chunk IDs stable.
    """
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")
    step = chunk_size - overlap
    spans: list[tuple[int, int, str]] = []
    n = len(text)
    if n == 0:
        return spans
    start = 0
    while start < n:
        end = min(start + chunk_size, n)
        spans.append((start, end, text[start:end]))
        if end == n:
            break
        start += step
    return spans


def build_corpus() -> list[Chunk]:
    """Re-chunk the source documents from disk (no cache)."""
    chunks: list[Chunk] = []
    for source_name, path in SOURCE_FILES.items():
        text = path.read_text(encoding="utf-8")
        spans = chunk_text(text)
        for i, (start, end, span_text) in enumerate(spans, start=1):
            chunk_id = f"{source_name}-{i:04d}"
            chunks.append(Chunk(id=chunk_id, source=source_name, start=start, end=end, text=span_text))
    return chunks


def load_or_build_chunks(force: bool = False) -> list[Chunk]:
    """Load chunks from the on-disk cache, rebuilding it if missing/forced.

    Note: this does NOT check source-file mtimes/hashes against the cache —
    if you edit requirements/prd.md or requirements/frd.md, pass force=True
    (or delete ai/corpus/chunks.json) to rebuild. Source docs are static
    within this task's scope so that's an acceptable simplification.
    """
    if not force and CHUNKS_CACHE.exists():
        raw = json.loads(CHUNKS_CACHE.read_text(encoding="utf-8"))
        return [Chunk(**c) for c in raw]
    chunks = build_corpus()
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    CHUNKS_CACHE.write_text(
        json.dumps([asdict(c) for c in chunks], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return chunks


def chunks_by_id(chunks: list[Chunk] | None = None) -> dict[str, Chunk]:
    chunks = chunks if chunks is not None else load_or_build_chunks()
    return {c.id: c for c in chunks}


if __name__ == "__main__":
    built = load_or_build_chunks(force=True)
    print(f"built {len(built)} chunks -> {CHUNKS_CACHE}")
    for c in built[:3]:
        print(c.id, c.source, len(c.text), repr(c.text[:60]))
