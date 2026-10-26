# src/findex/ranking.py
import numpy as np
from pydantic import BaseModel


class NumpyPostingList(BaseModel):
    """Структура для зберігання постінгів у вигляді щільних масивів NumPy int32."""
    doc_ids: np.ndarray
    frequencies: np.ndarray

    model_config = {"arbitrary_types_allowed": True}


def compute_bm25_vectorized(
    term_freqs: np.ndarray, 
    doc_lens: np.ndarray, 
    avg_dl: float, 
    k1: float = 1.5, 
    b: float = 0.75
) -> np.ndarray:
    """Векторизований розрахунок BM25 через масиви NumPy."""
    numerator = term_freqs * (k1 + 1.0)
    denominator = term_freqs + k1 * (1.0 - b + b * (doc_lens / avg_dl))
    return numerator / denominator


def get_top_k_indices(scores: np.ndarray, k: int) -> np.ndarray:
    """Швидкий вибір топ-k індексів документів за допомогою np.argpartition."""
    if len(scores) <= k:
        return np.argsort(scores)[::-1]
    part = np.argpartition(scores, -k)[-k:]
    return part[np.argsort(scores[part])[::-1]]


# === ЗОНА СУМІСНОСТІ ЗІ СТАРИМ КОДОМ (Щоб не падало з ImportError) ===

class BM25:
    """Сумісний клас для старого коду."""
    def __init__(self, *args, **kwargs):
        pass

class TfIdf:
    """Сумісний клас для старого коду."""
    def __init__(self, *args, **kwargs):
        pass

def rank_documents(*args, **kwargs):
    """Сумісна функція для старого коду."""
    return []