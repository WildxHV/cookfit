"""Portable fuzzy search.

Works identically on SQLite (dev) and Postgres (prod) by scoring in Python
rather than relying on pg_trgm. The catalog is small (hundreds of rows), so a
full scan with scoring is fast and good enough. Can be swapped for a DB-side
full-text/trigram index later without changing the API.
"""

from __future__ import annotations

from difflib import SequenceMatcher


def _ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def score_query(query: str, candidates: list[str]) -> float:
    """Best match score in [0, 1] of `query` against any candidate string.

    Scoring, strongest first:
      - exact match            -> 1.0
      - candidate startswith q -> 0.9 + small length bonus
      - q is a substring       -> 0.8 + small length bonus
      - else fuzzy ratio       -> SequenceMatcher ratio
    """
    q = query.strip().lower()
    if not q:
        return 0.0
    best = 0.0
    for cand in candidates:
        c = cand.strip().lower()
        if not c:
            continue
        if c == q:
            return 1.0
        if c.startswith(q):
            best = max(best, 0.9 + 0.1 * (len(q) / len(c)))
        elif q in c:
            best = max(best, 0.8 + 0.05 * (len(q) / len(c)))
        else:
            best = max(best, _ratio(q, c))
    return min(best, 1.0)


def rank(
    query: str,
    items: list,
    searchable: callable,
    limit: int = 20,
    threshold: float = 0.35,
) -> list:
    """Return up to `limit` items ranked by match score, dropping weak matches.

    `searchable(item) -> list[str]` yields the strings to match against
    (e.g. name + aliases).
    """
    scored = []
    for item in items:
        s = score_query(query, searchable(item))
        if s >= threshold:
            scored.append((s, item))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in scored[:limit]]
