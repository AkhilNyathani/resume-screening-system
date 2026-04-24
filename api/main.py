from __future__ import annotations

from os import getenv

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from api.model import CandidateDocument, ResumeRanker
from api.parser import clean_text, extract_resume_text


class RankedCandidate(BaseModel):
    rank: int
    candidate_name: str
    filename: str
    score: float
    similarity_score: float
    skill_match_score: float
    matching_strategy: str
    extracted_skills: list[str]
    education_keywords: list[str]
    experience_indicators: list[str]


class SkippedFile(BaseModel):
    filename: str
    reason: str


class RankResponse(BaseModel):
    status: str
    matching_strategy: str
    job_description_skills: list[str]
    ranked_candidates: list[RankedCandidate]
    skipped_files: list[SkippedFile]


app = FastAPI(
    title="Resume Screening and Candidate Ranking API",
    description="Ranks uploaded resumes against a job description using TF-IDF and optional semantic matching.",
    version="1.0.0",
)

allowed_origins = getenv("CORS_ALLOW_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins if origin.strip()],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

ranker = ResumeRanker()


@app.get("/")
def health_check() -> dict[str, str]:
    return {"status": "API running"}


@app.post("/rank", response_model=RankResponse)
async def rank_resumes(
    job_description: str = Form(...),
    resume_files: list[UploadFile] = File(...),
) -> RankResponse:
    if not job_description.strip():
        raise HTTPException(status_code=400, detail="job_description cannot be empty.")

    if not resume_files:
        raise HTTPException(status_code=400, detail="At least one resume file is required.")

    parsed_candidates: list[CandidateDocument] = []
    skipped_files: list[SkippedFile] = []

    for resume_file in resume_files:
        filename = resume_file.filename or "unknown_file"
        file_bytes = await resume_file.read()

        if not file_bytes:
            skipped_files.append(SkippedFile(filename=filename, reason="Uploaded file is empty."))
            continue

        try:
            raw_text = extract_resume_text(filename, file_bytes)
            cleaned_text = clean_text(raw_text)

            if not raw_text.strip():
                skipped_files.append(SkippedFile(filename=filename, reason="No readable text was found in the document."))
                continue

            parsed_candidates.append(
                CandidateDocument(
                    filename=filename,
                    raw_text=raw_text,
                    cleaned_text=cleaned_text,
                )
            )
        except ValueError as exc:
            skipped_files.append(SkippedFile(filename=filename, reason=str(exc)))
        except Exception:
            skipped_files.append(
                SkippedFile(
                    filename=filename,
                    reason="The file could not be processed. Please verify the document is not corrupted.",
                )
            )

    if not parsed_candidates:
        raise HTTPException(
            status_code=400,
            detail="No valid resumes were processed. Please upload at least one readable PDF, DOCX, or TXT file.",
        )

    try:
        ranked_candidates, matching_strategy, job_signals = ranker.rank_candidates(job_description, parsed_candidates)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return RankResponse(
        status="success",
        matching_strategy=matching_strategy,
        job_description_skills=job_signals["skills"],
        ranked_candidates=[RankedCandidate(**candidate) for candidate in ranked_candidates],
        skipped_files=skipped_files,
    )
