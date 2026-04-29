"""
Unified search backend.
Primary: PostgreSQL + pgvector against pouch_Items1.
Fallback: in-memory numpy store built from catalogue.json (works without Postgres).
The fallback is fast enough for < 50,000 records (full scan, ~2ms for 200 rows).
"""

import json
from pathlib import Path

import numpy as np

DATA_DIR        = Path(__file__).parent.parent / "data"
CATALOGUE_PATH  = DATA_DIR / "catalogue.json"
EMBEDDINGS_PATH = DATA_DIR / "embeddings.npy"

_records: list[dict] | None = None
_embeddings: np.ndarray | None = None


# ── File-based backend ────────────────────────────────────────────────────────

def save_file_store(records: list[dict], embeddings: list[np.ndarray]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    meta = [{k: v for k, v in r.items() if k != "embedding"} for r in records]
    with open(CATALOGUE_PATH, "w") as f:
        json.dump(meta, f)
    np.save(EMBEDDINGS_PATH, np.array(embeddings))
    print(f"File store saved -> {CATALOGUE_PATH}")


def _load_file_store() -> None:
    global _records, _embeddings
    if _records is not None:
        return
    if not CATALOGUE_PATH.exists():
        raise FileNotFoundError(
            "No catalogue found. Run 'python src/embed_pouch_items1.py' first."
        )
    with open(CATALOGUE_PATH) as f:
        _records = json.load(f)
    _embeddings = np.load(EMBEDDINGS_PATH)


def _search_in_memory(
    query_vec: np.ndarray,
    limit: int,
    food_safe_only: bool,
    material_type: str | None,
    zip_lock: str | None,
) -> list[dict]:
    _load_file_store()
    assert _records is not None and _embeddings is not None

    idx = [
        i for i, r in enumerate(_records)
        if (not food_safe_only or r.get("food_grade") == "yes" or r.get("food_safe") is True)
        and (material_type is None or r.get("material_type") == material_type)
        and (zip_lock is None or r.get("zip_lock") == zip_lock)
    ]
    if not idx:
        return []

    sims = _embeddings[idx] @ query_vec          # dot product = cosine sim (normalised)
    top  = np.argsort(sims)[::-1][:limit]

    return [
        {**_records[idx[j]], "similarity": round(float(sims[top[k]]), 4)}
        for k, j in enumerate(top)
    ]


# ── PostgreSQL backend (pouch_Items1) ─────────────────────────────────────────

def _search_pgvector(
    query_vec: np.ndarray,
    limit: int,
    food_safe_only: bool,
    material_type: str | None,
    zip_lock: str | None,
) -> list[dict]:
    from db import search_pouch_items1
    return search_pouch_items1(query_vec, limit, food_safe_only, material_type, zip_lock)


# ── Public interface ──────────────────────────────────────────────────────────

def search(
    query_vec: np.ndarray,
    limit: int = 5,
    food_safe_only: bool = False,
    material_type: str | None = None,
    zip_lock: str | None = None,
) -> list[dict]:
    try:
        results = _search_pgvector(query_vec, limit, food_safe_only, material_type, zip_lock)
        return results
    except Exception:
        return _search_in_memory(query_vec, limit, food_safe_only, material_type, zip_lock)
