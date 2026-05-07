import time
from typing import List, Optional

from app.config import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL, HF_API_TOKEN


_client = None


def get_client():
    global _client
    if _client is None:
        if not HF_API_TOKEN:
            raise RuntimeError(
                "HF_API_TOKEN is not configured. Set it in backend/.env to use the embedder."
            )
        from huggingface_hub import InferenceClient

        _client = InferenceClient(token=HF_API_TOKEN)
    return _client


def _coerce_to_vector(raw: object) -> List[float]:
    import numpy as np

    array = np.asarray(raw, dtype="float32")
    if array.ndim == 3:
        array = array[0]
    if array.ndim == 2:
        array = array.mean(axis=0)
    if array.ndim != 1:
        raise ValueError(f"Unexpected embedding shape from HF: {array.shape}")

    norm = float(np.linalg.norm(array))
    if norm > 0:
        array = array / norm

    if array.shape[0] != EMBEDDING_DIMENSIONS:
        raise ValueError(
            f"Embedding dimension mismatch: model returned {array.shape[0]} but config expects {EMBEDDING_DIMENSIONS}"
        )

    return array.tolist()


def embed_text(text: str, model: Optional[str] = None) -> List[float]:
    client = get_client()
    target_model = model or EMBEDDING_MODEL

    last_error: Optional[Exception] = None
    for attempt in range(3):
        try:
            result = client.feature_extraction(text, model=target_model)
            return _coerce_to_vector(result)
        except Exception as exc:  # broad to cover transient HF / network errors
            last_error = exc
            time.sleep(2 ** attempt)

    raise RuntimeError(f"HF embedding call failed after 3 attempts: {last_error}")


def embed_texts(texts: List[str], model: Optional[str] = None) -> List[List[float]]:
    return [embed_text(text, model=model) for text in texts]
