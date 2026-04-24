from __future__ import annotations

from functools import lru_cache
from typing import Iterable
import re

import spacy
from spacy.language import Language
from spacy.lang.en import English


SKILL_KEYWORDS = {
    "python",
    "java",
    "sql",
    "postgresql",
    "mysql",
    "mongodb",
    "redis",
    "fastapi",
    "flask",
    "django",
    "streamlit",
    "scikit-learn",
    "pandas",
    "numpy",
    "tensorflow",
    "pytorch",
    "machine learning",
    "deep learning",
    "natural language processing",
    "nlp",
    "llm",
    "data science",
    "data analysis",
    "statistics",
    "feature engineering",
    "mlops",
    "airflow",
    "spark",
    "kafka",
    "docker",
    "kubernetes",
    "terraform",
    "aws",
    "azure",
    "gcp",
    "git",
    "linux",
    "rest api",
    "microservices",
    "graphql",
    "node.js",
    "react",
    "typescript",
    "javascript",
    "ci/cd",
    "unit testing",
    "pytest",
    "bert",
    "transformers",
    "computer vision",
    "etl",
}

EDUCATION_KEYWORDS = {
    "bachelor",
    "master",
    "phd",
    "b.tech",
    "m.tech",
    "b.e",
    "m.s",
    "mba",
    "degree",
    "university",
    "college",
    "computer science",
    "engineering",
    "artificial intelligence",
    "data science",
}

EXPERIENCE_TERMS = {
    "experience",
    "internship",
    "senior",
    "lead",
    "managed",
    "ownership",
    "delivered",
    "deployed",
    "production",
    "mentor",
}

EXPERIENCE_PATTERNS = (
    r"\b\d+\+?\s+(?:years|year|yrs)\b",
    r"\b\d+\+?\s+(?:months|month)\b",
    r"\bmore than \d+\s+years\b",
)


@lru_cache(maxsize=1)
def get_nlp() -> Language:
    try:
        return spacy.load("en_core_web_sm", disable=["parser", "ner", "lemmatizer"])
    except OSError:
        nlp = English()
        if "sentencizer" not in nlp.pipe_names:
            nlp.add_pipe("sentencizer")
        return nlp


def normalize_for_matching(text: str) -> str:
    text = text.lower().replace("-", " ")
    text = re.sub(r"[^a-z0-9+#./\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_keywords(text: str, keywords: Iterable[str]) -> list[str]:
    normalized_text = normalize_for_matching(text)
    doc = get_nlp()(normalized_text)
    tokens = {token.text for token in doc if not token.is_space}

    matches: set[str] = set()
    for keyword in keywords:
        normalized_keyword = normalize_for_matching(keyword)
        if " " in normalized_keyword or any(char in normalized_keyword for char in "+#/."):
            if normalized_keyword in normalized_text:
                matches.add(keyword)
        elif normalized_keyword in tokens:
            matches.add(keyword)

    return sorted(matches)


def extract_experience_indicators(text: str) -> list[str]:
    normalized_text = normalize_for_matching(text)
    matches: set[str] = set()

    for pattern in EXPERIENCE_PATTERNS:
        matches.update(re.findall(pattern, normalized_text))

    for term in EXPERIENCE_TERMS:
        if term in normalized_text:
            matches.add(term)

    return sorted(matches)


def extract_profile_signals(text: str) -> dict[str, list[str]]:
    return {
        "skills": extract_keywords(text, SKILL_KEYWORDS),
        "education_keywords": extract_keywords(text, EDUCATION_KEYWORDS),
        "experience_indicators": extract_experience_indicators(text),
    }


def compute_skill_match(resume_skills: Iterable[str], job_description_skills: Iterable[str]) -> float:
    resume_skill_set = {skill.lower() for skill in resume_skills}
    job_skill_set = {skill.lower() for skill in job_description_skills}

    if not job_skill_set:
        return 0.0

    overlap = resume_skill_set.intersection(job_skill_set)
    return len(overlap) / len(job_skill_set)


def candidate_name_from_filename(filename: str) -> str:
    stem = re.sub(r"\.[^.]+$", "", filename)
    stem = stem.replace("_", " ").replace("-", " ").strip()
    if not stem:
        return "Unknown Candidate"

    candidate_name = stem.title()
    replacements = {
        " Ml ": " ML ",
        " Nlp ": " NLP ",
        " Ai ": " AI ",
        " Api ": " API ",
    }

    candidate_name = f" {candidate_name} "
    for source, target in replacements.items():
        candidate_name = candidate_name.replace(source, target)

    return candidate_name.strip()
