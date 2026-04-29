"""
Sentence-transformer embedding wrapper.
Model: all-MiniLM-L6-v2 (384-dim, ~22ms/query on CPU).
Downloaded automatically on first use (~90 MB).
"""

from sentence_transformers import SentenceTransformer
import numpy as np

_model: SentenceTransformer | None = None


def load_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print("Loading embedding model (all-MiniLM-L6-v2)...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print("Embedding model ready.")
    return _model


def embed(text: str) -> np.ndarray:
    return load_model().encode(text, normalize_embeddings=True)


def embed_batch(texts: list[str], show_progress: bool = False) -> list[np.ndarray]:
    return load_model().encode(
        texts,
        normalize_embeddings=True,
        batch_size=64,
        show_progress_bar=show_progress,
    )
