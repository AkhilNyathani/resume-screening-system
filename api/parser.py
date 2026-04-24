from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re

import pdfplumber
from docx import Document
from spacy.lang.en.stop_words import STOP_WORDS


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def extract_resume_text(filename: str, file_bytes: bytes) -> str:
    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{extension or 'unknown'}'. "
            "Only PDF, DOCX, and TXT files are supported."
        )

    if extension == ".pdf":
        text = _extract_pdf_text(file_bytes)
    elif extension == ".docx":
        text = _extract_docx_text(file_bytes)
    else:
        text = _extract_txt_text(file_bytes)

    return text.strip()


def clean_text(text: str) -> str:
    normalized_text = text.lower().replace("-", " ")
    normalized_text = re.sub(r"[^a-z0-9+#./\s]", " ", normalized_text)
    normalized_text = re.sub(r"\s+", " ", normalized_text).strip()

    cleaned_tokens: list[str] = []
    for token in normalized_text.split():
        candidate = token.strip(".")
        if candidate in STOP_WORDS:
            continue
        if len(candidate) == 1 and candidate not in {"c", "r"}:
            continue
        cleaned_tokens.append(candidate)

    return " ".join(cleaned_tokens)


def _extract_pdf_text(file_bytes: bytes) -> str:
    pages: list[str] = []
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages.append(page_text)
    return "\n".join(pages)


def _extract_docx_text(file_bytes: bytes) -> str:
    document = Document(BytesIO(file_bytes))
    paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
    return "\n".join(paragraphs)


def _extract_txt_text(file_bytes: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return file_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    return file_bytes.decode("utf-8", errors="ignore")
