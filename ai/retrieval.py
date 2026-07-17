"""ai/retrieval.py — top-k retrieval for FR-017 FAQ RAG.

Config (eval/thresholds.yaml, do not change without an ADR): top_k=5,
retriever=mmr.

Implements real Maximal Marginal Relevance (MMR) over cosine similarity —
not a "pretend MMR that's actually plain top-k". The corpus here is small
(139 chunks total, see ai/corpus/chunks.json) so the extra O(top_k * N)
MMR bookkeeping is cheap; there was no engineering reason to fall back to
plain similarity, unlike what might be true for a much larger corpus.

lambda_ (relevance vs. diversity trade-off, standard MMR formulation) is
set to 0.7, favoring relevance — this is a FAQ over a fairly small, mostly
non-redundant document pair (PRD+FRD), so diversity matters less than in a
web-search-style MMR use case. This value isn't pinned by thresholds.yaml
so it's not an ADR-restricted parameter, but it is a real design choice
worth calling out if it needs tuning later.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ai.corpus import Chunk, load_or_build_chunks
from ai.embeddings import embed_query, load_or_build_embeddings

TOP_K = 5  # eval/thresholds.yaml config.top_k
MMR_LAMBDA = 0.7


@dataclass
class Hit:
    chunk_id: str
    text: str
    score: float  # pure query-similarity score (pre-MMR-reranking), used for the no-evidence gate


def _cosine_sim_matrix(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    q = query_vec / (np.linalg.norm(query_vec) + 1e-12)
    m = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-12)
    return m @ q


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-12
    return float(np.dot(a, b) / denom)


def mmr_select(
    query_vec: np.ndarray,
    matrix: np.ndarray,
    ids: list[str],
    top_k: int,
    lambda_: float = MMR_LAMBDA,
    candidate_pool: int = 30,
) -> list[tuple[int, float]]:
    """Real MMR: iteratively pick the index maximizing
    lambda*sim(candidate, query) - (1-lambda)*max_sim(candidate, already_selected).

    Restricts the candidate pool to the top `candidate_pool` by pure cosine
    similarity first (cheap prefilter) — for this corpus size that's a
    no-op most of the time (candidate_pool=30 > top_k=5 always considered),
    it's just there so this doesn't silently become O(top_k * full_corpus)
    if the corpus grows a lot later.

    Returns list of (index_into_matrix, pure_query_similarity_score) in
    MMR-selection order, length top_k (or fewer if the corpus is smaller).
    """
    sims = _cosine_sim_matrix(query_vec, matrix)
    pool_size = min(candidate_pool, len(ids))
    pool = list(np.argsort(-sims)[:pool_size])

    selected: list[int] = []
    selected_vecs: list[np.ndarray] = []
    remaining = set(pool)

    while remaining and len(selected) < top_k:
        best_idx = None
        best_mmr = -1e18
        for idx in remaining:
            relevance = sims[idx]
            if selected_vecs:
                diversity_penalty = max(_cosine_sim(matrix[idx], sv) for sv in selected_vecs)
            else:
                diversity_penalty = 0.0
            mmr_score = lambda_ * relevance - (1 - lambda_) * diversity_penalty
            if mmr_score > best_mmr:
                best_mmr = mmr_score
                best_idx = idx
        selected.append(best_idx)
        selected_vecs.append(matrix[best_idx])
        remaining.discard(best_idx)

    return [(idx, float(sims[idx])) for idx in selected]


def retrieve(question: str, top_k: int = TOP_K) -> list[Hit]:
    """Embed `question` and return up to top_k Hits selected via MMR.

    Hit.score is the *pure cosine similarity to the query* (not the MMR
    objective value) — that's what the no-evidence gate in ai/pipeline.py
    thresholds on, since MMR-adjusted scores aren't comparable across
    queries the way plain relevance is.
    """
    chunks = load_or_build_chunks()
    by_id = {c.id: c for c in chunks}
    ids, matrix = load_or_build_embeddings()

    query_vec = np.array(embed_query(question), dtype=np.float32)
    selected = mmr_select(query_vec, matrix, ids, top_k)

    hits = []
    for idx, score in selected:
        cid = ids[idx]
        hits.append(Hit(chunk_id=cid, text=by_id[cid].text, score=score))
    return hits


def _self_check() -> None:
    """Assert-based self-check for mmr_select(), run when this module is
    executed directly. Pure numpy, no API calls -- mmr_select is
    deterministic, dependency-free logic, so this doesn't need (and
    shouldn't need) a live embedding call to validate. No pytest in this
    repo (confirmed convention); matches the project's existing pattern of
    assert-based self-verification in standalone scripts.
    """
    rng = np.random.default_rng(42)  # fixed seed -> reproducible check
    n, dims = 30, 16
    matrix = rng.normal(size=(n, dims)).astype(np.float32)
    ids = [f"c{i}" for i in range(n)]
    query = rng.normal(size=(dims,)).astype(np.float32)

    # 1. lambda_=1.0 must degrade to plain top-k similarity ranking: the
    #    diversity penalty term is weighted by (1-lambda_)=0, so MMR's
    #    selection order should exactly match sorting by pure cosine
    #    similarity to the query.
    selected = mmr_select(query, matrix, ids, top_k=5, lambda_=1.0, candidate_pool=n)
    actual_order = [idx for idx, _ in selected]
    sims = _cosine_sim_matrix(query, matrix)
    expected_order = list(np.argsort(-sims)[:5])
    assert actual_order == expected_order, (
        f"lambda_=1.0 should match plain top-k ranking: got {actual_order}, expected {expected_order}"
    )

    # 2. MMR must never select the same index twice, at any lambda_.
    for lambda_ in (0.0, 0.3, 0.7, 1.0):
        selected = mmr_select(query, matrix, ids, top_k=10, lambda_=lambda_, candidate_pool=n)
        idxs = [idx for idx, _ in selected]
        assert len(idxs) == len(set(idxs)), f"mmr_select (lambda_={lambda_}) selected the same index twice: {idxs}"
        assert len(idxs) == 10, f"mmr_select should return top_k={10} indices, got {len(idxs)}"

    print(f"ai/retrieval.py mmr_select self-check: PASS (n={n} synthetic vectors, dims={dims})")


if __name__ == "__main__":
    import sys

    _self_check()

    q = sys.argv[1] if len(sys.argv) > 1 else "공급업체 등급은 어떻게 산정되나요?"
    for h in retrieve(q):
        print(f"{h.chunk_id}  score={h.score:.4f}  {h.text[:60]!r}")
