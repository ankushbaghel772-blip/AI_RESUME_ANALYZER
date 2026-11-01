"""Local Sentence Transformer similarity for a resume and a target job description."""

from __future__ import annotations

import logging
from pathlib import Path
from threading import Lock

import numpy as np


logger = logging.getLogger(__name__)
MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_PATH = Path(__file__).resolve().parents[2] / "ml" / "models" / "bert_resume_matcher"
_model_lock = Lock()
_model = None


def _load_model():
    """Load the bundled model once; never download weights during a web request."""
    global _model
    if not (MODEL_PATH / "modules.json").is_file():
        raise FileNotFoundError(f"Bundled Sentence Transformer not found at {MODEL_PATH}")
    with _model_lock:
        if _model is not None:
            return _model
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(str(MODEL_PATH), device="cpu")
        return _model


def _document_embedding(text: str, model) -> np.ndarray:
    """Encode all document chunks so long resumes are not silently truncated."""
    token_ids = model.tokenizer.encode(text, add_special_tokens=False)
    if not token_ids:
        raise ValueError("Text contains no tokens for semantic matching.")
    chunk_size = max(1, int(model.max_seq_length) - 2)
    token_chunks = [token_ids[i : i + chunk_size] for i in range(0, len(token_ids), chunk_size)]
    text_chunks = [
        model.tokenizer.decode(
            chunk, skip_special_tokens=True, clean_up_tokenization_spaces=True
        )
        for chunk in token_chunks
    ]
    vectors = model.encode(
        text_chunks,
        batch_size=16,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    weights = np.asarray([len(chunk) for chunk in token_chunks], dtype=np.float32)
    vector = np.average(np.asarray(vectors, dtype=np.float32), axis=0, weights=weights)
    norm = float(np.linalg.norm(vector))
    if norm == 0:
        raise ValueError("The model returned an empty embedding.")
    return vector / norm


def score_resume_job(resume_text: str, job_description: str) -> dict:
    """Return a raw cosine similarity signal, separate from the rule-based ATS score."""
    if not resume_text or not resume_text.strip() or not job_description or not job_description.strip():
        return {"available": False, "message": "Resume text and job description are both required."}
    try:
        model = _load_model()
        resume_vector = _document_embedding(resume_text, model)
        job_vector = _document_embedding(job_description, model)
        similarity = float(np.clip(np.dot(resume_vector, job_vector), -1.0, 1.0))
        return {
            "available": True,
            "cosine_similarity": round(similarity, 4),
            "model_name": MODEL_ID,
            "model_type": "pretrained_sentence_transformer",
            "fine_tuned": False,
            "interpretation": "Uncalibrated semantic similarity; not a probability, percentage, or hiring decision.",
        }
    except Exception as exc:
        logger.warning("Sentence Transformer matching unavailable: %s", exc)
        return {
            "available": False,
            "message": "Semantic matching is unavailable. See the BERT setup instructions.",
        }
