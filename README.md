# Resume Screening and Candidate Ranking System

## Project Overview
This project provides a production-ready resume screening workflow built with FastAPI and Streamlit. Recruiters or hiring teams can upload multiple resumes, submit a target job description, and receive a ranked candidate list with similarity scores and extracted skills.

The system uses a clean separation between the API layer, parsing utilities, NLP feature extraction, and the user interface. It is designed for straightforward deployment on Render for the backend and Streamlit Cloud for the frontend.

## Features
- Upload multiple resumes in PDF, DOCX, or TXT format
- Parse and clean resume text with modular file handlers
- Extract skills, education keywords, and experience indicators
- Rank candidates using TF-IDF and cosine similarity
- Auto-enable semantic similarity with `sentence-transformers` when available
- Combine similarity score and skill match score into a final ranking
- Display ranked candidates and score charts in Streamlit
- Deploy backend and frontend separately with minimal configuration

## Tech Stack
- Backend: FastAPI
- Frontend: Streamlit
- NLP/ML: scikit-learn, spaCy
- Optional semantic matching: sentence-transformers
- File parsing: pdfplumber, python-docx
- Deployment: Render, Streamlit Cloud

## Architecture Diagram
```text
                 +---------------------------+
                 |        Streamlit UI       |
                 |  Upload resumes + JD      |
                 +-------------+-------------+
                               |
                               | HTTP POST /rank
                               v
                 +---------------------------+
                 |        FastAPI API        |
                 |  Validation + Orchestration
                 +-------------+-------------+
                               |
             +-----------------+-----------------+
             |                                   |
             v                                   v
 +--------------------------+         +--------------------------+
 |      parser.py           |         |        utils.py          |
 | PDF / DOCX / TXT parsing |         | skills / education / exp |
 | text cleaning            |         | keyword extraction       |
 +-------------+------------+         +-------------+------------+
               |                                    |
               +-----------------+------------------+
                                 |
                                 v
                    +---------------------------+
                    |         model.py          |
                    | TF-IDF + optional semantic|
                    | scoring and ranking       |
                    +-------------+-------------+
                                  |
                                  v
                    +---------------------------+
                    | Ranked candidate response |
                    +---------------------------+
```

## Project Structure
```text
resume-screening-system/
|
|-- api/
|   |-- main.py
|   |-- model.py
|   |-- utils.py
|   |-- parser.py
|   `-- requirements.txt
|
|-- app/
|   |-- app.py
|   `-- requirements.txt
|
|-- data/
|   |-- sample_job_description.txt
|   `-- sample_resumes/
|
|-- README.md
|-- .gitignore
`-- render.yaml
```

## Installation
### 1. Clone the repository
```bash
git clone https://github.com/AkhilNyathani/resume-screening-system.git
cd resume-screening-system
```

### 2. Create a backend virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r api/requirements.txt
```

### 3. Create a frontend environment if desired
You can reuse the same virtual environment or create a separate one:

```bash
pip install -r app/requirements.txt
```

### 4. Optional semantic matching
The application automatically falls back to TF-IDF if `sentence-transformers` is not installed or if the model cannot be loaded.

Optional install:

```bash
pip install sentence-transformers
```

## Running Backend
From the project root:

```bash
uvicorn api.main:app --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/
```

Expected response:

```json
{"status":"API running"}
```

## Running Frontend
Set the API URL first. The Streamlit app is intentionally configured to use an environment variable instead of a hardcoded localhost URL.

PowerShell example:

```powershell
$env:API_URL="https://your-render-backend-url.onrender.com"
streamlit run app/app.py
```

If you want to run the frontend against a local backend during development, set `API_URL` manually to your local server before launching Streamlit.

## Deployment Steps
### Render Backend
1. Push the repository to GitHub.
2. Sign in to [Render](https://render.com/).
3. Click **New +** and select **Blueprint** or **Web Service**.
4. Connect your GitHub repository.
5. If you use **Blueprint**, Render will read `render.yaml` automatically.
6. If you create the service manually, use:
   - Build Command: `pip install -r api/requirements.txt`
   - Start Command: `uvicorn api.main:app --host 0.0.0.0 --port 10000`
7. Set any optional environment variables:
   - `CORS_ALLOW_ORIGINS`
   - `SENTENCE_TRANSFORMER_MODEL`
8. Deploy and copy the public Render URL.

### Streamlit Cloud Frontend
1. Sign in to [Streamlit Community Cloud](https://streamlit.io/cloud).
2. Create a new app from the same GitHub repository.
3. Set the app entry point to `app/app.py`.
4. In app settings or secrets, define:

```toml
API_URL = "https://your-render-backend-url.onrender.com"
```

5. For dependencies, Streamlit Cloud should use `app/requirements.txt`.
6. Deploy the app and verify the upload flow.

## API Documentation
### `GET /`
Health check endpoint.

Response:

```json
{
  "status": "API running"
}
```

### `POST /rank`
Ranks multiple resumes against a job description.

Request type:
- `multipart/form-data`

Fields:
- `job_description`: string
- `resume_files`: one or more files in PDF, DOCX, or TXT format

Response fields:
- `status`
- `matching_strategy`
- `job_description_skills`
- `ranked_candidates`
- `skipped_files`

Swagger UI is available locally at:

```text
http://127.0.0.1:8000/docs
```

## Example Inputs/Outputs
### Example job description
Use the file at `data/sample_job_description.txt`.

### Example sample resumes
- `data/sample_resumes/alexandra_reed_ml_engineer.txt`
- `data/sample_resumes/michael_chen_data_scientist.txt`
- `data/sample_resumes/sophia_patel_backend_engineer.txt`

### Example `curl` request
```bash
curl -X POST "http://127.0.0.1:8000/rank" \
  -F "job_description=Senior Machine Learning Engineer with FastAPI, scikit-learn, spaCy, Docker, and AWS experience." \
  -F "resume_files=@data/sample_resumes/alexandra_reed_ml_engineer.txt" \
  -F "resume_files=@data/sample_resumes/michael_chen_data_scientist.txt" \
  -F "resume_files=@data/sample_resumes/sophia_patel_backend_engineer.txt"
```

### Example JSON response
```json
{
  "status": "success",
  "matching_strategy": "tfidf",
  "job_description_skills": ["aws", "docker", "fastapi", "machine learning", "nlp", "python", "scikit-learn", "spacy", "transformers"],
  "ranked_candidates": [
    {
      "rank": 1,
      "candidate_name": "Alexandra Reed ML Engineer",
      "filename": "alexandra_reed_ml_engineer.txt",
      "score": 0.8964,
      "similarity_score": 0.8705,
      "skill_match_score": 1.0,
      "matching_strategy": "tfidf",
      "extracted_skills": ["aws", "ci/cd", "docker", "fastapi", "feature engineering", "machine learning", "nlp", "postgresql", "python", "scikit-learn", "spacy", "streamlit", "transformers", "unit testing"],
      "education_keywords": ["bachelor", "computer science", "engineering", "master"],
      "experience_indicators": ["6 years", "delivered", "experience", "lead", "production"]
    }
  ],
  "skipped_files": []
}
```

## Notes
- The backend keeps semantic matching optional to avoid breaking deployment when no transformer model is available.
- CORS is enabled and can be restricted through `CORS_ALLOW_ORIGINS`.
- The sample data in `data/` is included to speed up local testing and demos.
