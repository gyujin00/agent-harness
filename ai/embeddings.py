"""ai/embeddings.py — OpenAI embedding calls + on-disk cache for FR-017 RAG.

Model is `text-embedding-3-small` (eval/thresholds.yaml config.embedding_model)
— changing it requires an ADR (agent-specs/ai-worker.spec.md decision rule).

Embeddings are cached to ai/corpus/embeddings.npy (float32 matrix, row i
corresponds to the i-th chunk in ai/corpus/chunks.json) plus a small
ai/corpus/embeddings_meta.json recording the model name and the exact chunk
ID order the matrix was built against, so a stale cache (e.g. after editing
the source docs and rebuilding chunks.json) is detected instead of silently
misaligned. The cache is NOT committed to git (see ai/.gitignore) — it's
derived, regenerable data and, more importantly, real OpenAI API spend we
don't want to force reviewers/CI to redo just to check out the branch.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ai.corpus import Chunk, CORPUS_DIR, load_or_build_chunks
from ai.llm_client import get_client

EMBEDDINGS_CACHE = CORPUS_DIR / "embeddings.npy"
EMBEDDINGS_META = CORPUS_DIR / "embeddings_meta.json"

EMBEDDING_MODEL = "text-embedding-3-small"  # eval/thresholds.yaml config.embedding_model


def embed_texts(texts: list[str], model: str = EMBEDDING_MODEL, batch_size: int = 100) -> list[list[float]]:
    """Embed a list of texts via the real OpenAI Embeddings API, batched."""
    client = get_client()
    out: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        resp = client.embeddings.create(model=model, input=batch)
        # API returns results in the same order as input.
        out.extend([d.embedding for d in resp.data])
    return out


def embed_query(text: str, model: str = EMBEDDING_MODEL) -> list[float]:
    return embed_texts([text], model=model)[0]


def build_embeddings(chunks: list[Chunk] | None = None) -> tuple[list[str], np.ndarray]:
    """Embed every chunk (real API calls) and cache the result to disk."""
    chunks = chunks if chunks is not None else load_or_build_chunks()
    ids = [c.id for c in chunks]
    texts = [c.text for c in chunks]
    vectors = embed_texts(texts)
    matrix = np.array(vectors, dtype=np.float32)

    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    np.save(EMBEDDINGS_CACHE, matrix)
    EMBEDDINGS_META.write_text(
        json.dumps({"model": EMBEDDING_MODEL, "chunk_ids": ids, "dims": matrix.shape[1]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return ids, matrix


def load_or_build_embeddings(force: bool = False) -> tuple[list[str], np.ndarray]:
    """Load the cached embedding matrix, rebuilding (real API calls) if
    missing, forced, or if it's out of sync with the current chunk ID list
    (e.g. corpus was rebuilt after a source-doc edit).
    """
    chunks = load_or_build_chunks()
    current_ids = [c.id for c in chunks]

    if not force and EMBEDDINGS_CACHE.exists() and EMBEDDINGS_META.exists():
        meta = json.loads(EMBEDDINGS_META.read_text(encoding="utf-8"))
        if meta.get("model") == EMBEDDING_MODEL and meta.get("chunk_ids") == current_ids:
            matrix = np.load(EMBEDDINGS_CACHE)
            return current_ids, matrix
        # cache is stale (chunk set changed or model changed) -> rebuild.

    return build_embeddings(chunks)


if __name__ == "__main__":
    ids, matrix = load_or_build_embeddings()
    print(f"embeddings: {matrix.shape} for {len(ids)} chunks, model={EMBEDDING_MODEL}")
