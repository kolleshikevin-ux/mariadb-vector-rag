"""Generate normalized 384-dimensional text embeddings."""

from __future__ import annotations

from functools import lru_cache
import math
import os
from typing import Iterable

MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)
EMBEDDING_DIMENSION = 384


@lru_cache(maxsize=1)
def _get_model():
    """Load and cache the SentenceTransformer model on first use."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "sentence-transformers is not installed. Install the project dependencies "
            "with 'pip install -r requirements.txt'."
        ) from exc

    device = os.getenv("EMBEDDING_DEVICE")
    if device:
        return SentenceTransformer(MODEL_NAME, device=device)
    return SentenceTransformer(MODEL_NAME)


def embed_texts(texts: Iterable[str]) -> list[list[float]]:
    """Encode multiple texts as normalized float vectors."""
    cleaned_texts: list[str] = []
    for index, text in enumerate(texts):
        if not isinstance(text, str) or not text.strip():
            raise ValueError(
                f"Text at position {index} is empty or is not a valid string."
            )
        cleaned_texts.append(text.strip())

    if not cleaned_texts:
        return []

    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(
            "numpy is not installed. Install the project dependencies first."
        ) from exc

    encoded_vectors = _get_model().encode(
        cleaned_texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=len(cleaned_texts) > 4,
    )
    embedding_matrix = np.asarray(encoded_vectors, dtype=np.float32)

    if embedding_matrix.ndim == 1 and len(cleaned_texts) == 1:
        embedding_matrix = embedding_matrix.reshape(1, -1)

    expected_shape = (len(cleaned_texts), EMBEDDING_DIMENSION)
    if embedding_matrix.shape != expected_shape:
        raise ValueError(
            f"The model returned shape {embedding_matrix.shape}; expected {expected_shape}. "
            "The MariaDB column is defined as VECTOR(384)."
        )
    if not np.isfinite(embedding_matrix).all():
        raise ValueError("The model returned an embedding containing NaN or infinity.")

    return embedding_matrix.tolist()


def embed_text(text: str) -> list[float]:
    """Encode one text and return exactly 384 normalized float values."""
    return embed_texts([text])[0]


def vector_to_text(vector: Iterable[float]) -> str:
    """Convert a vector to MariaDB's VEC_FromText array representation."""
    try:
        values = [float(value) for value in vector]
    except (TypeError, ValueError) as exc:
        raise ValueError("The embedding must be a sequence of numeric values.") from exc

    if len(values) != EMBEDDING_DIMENSION:
        raise ValueError(
            f"Invalid embedding dimension: {len(values)}; "
            f"expected {EMBEDDING_DIMENSION}."
        )
    if not all(math.isfinite(value) for value in values):
        raise ValueError("The embedding contains NaN or infinity.")

    return "[" + ",".join(format(value, ".9g") for value in values) + "]"


if __name__ == "__main__":
    sample_vector = embed_text("What is a database index?")
    print(f"Model: {MODEL_NAME}")
    print(f"Dimensions: {len(sample_vector)}")
    print(f"First 10 values: {sample_vector[:10]}")
    vector_norm = sum(value * value for value in sample_vector) ** 0.5
    print(f"Normalized length: {vector_norm:.6f}")
