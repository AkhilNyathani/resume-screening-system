from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd
import requests
import streamlit as st


DEFAULT_API_URL = "https://resume-screening-system-n7ps.onrender.com"


def get_api_url() -> str:
    if "API_URL" in st.secrets:
        return str(st.secrets["API_URL"]).rstrip("/")
    return os.getenv("API_URL", DEFAULT_API_URL).rstrip("/")


def guess_content_type(filename: str) -> str:
    extension = Path(filename).suffix.lower()
    if extension == ".pdf":
        return "application/pdf"
    if extension == ".docx":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return "text/plain"


def rank_candidates(api_url: str, job_description: str, uploaded_files: list[Any]) -> dict:
    files = [
        (
            "resume_files",
            (
                uploaded_file.name,
                uploaded_file.getvalue(),
                guess_content_type(uploaded_file.name),
            ),
        )
        for uploaded_file in uploaded_files
    ]

    response = requests.post(
        f"{api_url}/rank",
        data={"job_description": job_description},
        files=files,
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


st.set_page_config(
    page_title="Resume Screening and Candidate Ranking",
    layout="wide",
)

api_url = get_api_url()

st.title("Resume Screening and Candidate Ranking System")
st.caption("Upload candidate resumes, provide a job description, and rank applicants by fit.")

with st.sidebar:
    st.subheader("Configuration")
    st.code(api_url, language="text")
    st.info("Set `API_URL` in Streamlit secrets or environment variables to point at the deployed FastAPI service.")

job_description = st.text_area(
    "Job Description",
    height=240,
    placeholder="Paste the target job description here...",
)

uploaded_files = st.file_uploader(
    "Upload Resumes",
    type=["pdf", "docx", "txt"],
    accept_multiple_files=True,
)

if st.button("Rank Candidates", type="primary", use_container_width=True):
    if api_url == DEFAULT_API_URL:
        st.error("Set `API_URL` to your deployed Render backend before ranking candidates.")
    elif not job_description.strip():
        st.error("Enter a job description before submitting.")
    elif not uploaded_files:
        st.error("Upload at least one resume file.")
    else:
        with st.spinner("Analyzing resumes and ranking candidates..."):
            try:
                payload = rank_candidates(api_url, job_description, uploaded_files)
            except requests.HTTPError as exc:
                error_detail = exc.response.text if exc.response is not None else str(exc)
                st.error(f"Backend request failed: {error_detail}")
            except requests.RequestException as exc:
                st.error(f"Unable to reach the backend API: {exc}")
            else:
                ranked_candidates = payload.get("ranked_candidates", [])

                if not ranked_candidates:
                    st.warning("No ranked candidates were returned.")
                else:
                    results_frame = pd.DataFrame(
                        [
                            {
                                "Candidate Name": candidate["candidate_name"],
                                "Score": candidate["score"],
                                "Similarity Score": candidate["similarity_score"],
                                "Skill Match Score": candidate["skill_match_score"],
                                "Extracted Skills": ", ".join(candidate["extracted_skills"]),
                            }
                            for candidate in ranked_candidates
                        ]
                    )

                    st.subheader("Ranked Candidates")
                    st.dataframe(results_frame, use_container_width=True)

                    chart_frame = results_frame.set_index("Candidate Name")[["Score"]]
                    st.subheader("Score Comparison")
                    st.bar_chart(chart_frame)

                    with st.expander("Ranking Details", expanded=False):
                        st.write("Matching strategy:", payload.get("matching_strategy", "unknown"))
                        st.write(
                            "Job description skills:",
                            ", ".join(payload.get("job_description_skills", [])) or "No explicit skills detected.",
                        )

                        skipped_files = payload.get("skipped_files", [])
                        if skipped_files:
                            st.write("Skipped files:")
                            st.json(skipped_files)
