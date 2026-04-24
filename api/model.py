from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from parser import clean_text
from utils import candidate_name_from_filename, compute_skill_match, extract_profile_signals


@dataclass(slots=True)
class CandidateDocument:
    filename: str
    raw_text: str
    cleaned_text: str


@lru_cache(maxsize=1)
def get_sentence_transformer():
    try:
        from sentence_transformers import SentenceTransformer
    except Exception:
        return None

    model_name = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")

    try:
        return SentenceTransformer(model_name)
    except Exception:
        return None


class ResumeRanker:
    def __init__(self) -> None:
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))

    def rank_candidates(
        self,
        job_description: str,
        candidates: list[CandidateDocument],
    ) -> tuple[list[dict[str, object]], str, dict[str, list[str]]]:
        if not job_description.strip():
            raise ValueError("Job description cannot be empty.")
        if not candidates:
            raise ValueError("At least one parsed resume is required.")

        job_signals = extract_profile_signals(job_description)
        job_feature_text = clean_text(job_description) or job_description
        candidate_feature_texts = [candidate.cleaned_text or candidate.raw_text for candidate in candidates]
        tfidf_scores = self._compute_tfidf_scores(job_feature_text, candidate_feature_texts)
        semantic_scores = self._compute_semantic_scores(job_description, [candidate.raw_text for candidate in candidates])

        matching_strategy = "tfidf"
        if semantic_scores is not None:
            matching_strategy = "semantic+tfidf"

        weighted_results: list[dict[str, object]] = []
        job_has_skills = bool(job_signals["skills"])

        for index, candidate in enumerate(candidates):
            signals = extract_profile_signals(candidate.raw_text)
            tfidf_score = tfidf_scores[index]
            semantic_score = semantic_scores[index] if semantic_scores is not None else None

            similarity_score = tfidf_score
            if semantic_score is not None:
                similarity_score = (0.45 * tfidf_score) + (0.55 * semantic_score)

            skill_match_score = compute_skill_match(signals["skills"], job_signals["skills"])
            final_score = similarity_score if not job_has_skills else (0.8 * similarity_score) + (0.2 * skill_match_score)

            weighted_results.append(
                {
                    "candidate_name": candidate_name_from_filename(candidate.filename),
                    "filename": candidate.filename,
                    "score": round(final_score, 4),
                    "similarity_score": round(similarity_score, 4),
                    "skill_match_score": round(skill_match_score, 4),
                    "matching_strategy": "semantic+tfidf" if semantic_score is not None else "tfidf",
                    "extracted_skills": signals["skills"],
                    "education_keywords": signals["education_keywords"],
                    "experience_indicators": signals["experience_indicators"],
                }
            )

        ranked_results = sorted(weighted_results, key=lambda item: item["score"], reverse=True)
        for rank, result in enumerate(ranked_results, start=1):
            result["rank"] = rank

        return ranked_results, matching_strategy, job_signals

    def _compute_tfidf_scores(self, job_description: str, resume_texts: list[str]) -> list[float]:
        document_matrix = self.vectorizer.fit_transform([job_description, *resume_texts])
        similarity_matrix = cosine_similarity(document_matrix[0:1], document_matrix[1:])
        return similarity_matrix.flatten().tolist()

    def _compute_semantic_scores(self, job_description: str, resume_texts: list[str]) -> list[float] | None:
        sentence_transformer = get_sentence_transformer()
        if sentence_transformer is None:
            return None

        embeddings = sentence_transformer.encode(
            [job_description, *resume_texts],
            normalize_embeddings=True,
        )
        semantic_matrix = cosine_similarity([embeddings[0]], embeddings[1:])
        return semantic_matrix.flatten().tolist()
