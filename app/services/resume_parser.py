"""
Resume Parser Service
- Extracts plain text from PDF (pdfplumber) and DOCX (python-docx)
- Extracts style snapshot: tone, avg sentence length, vocabulary richness
"""
import io
import json
import re
from typing import Optional

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from docx import Document
except ImportError:
    Document = None


async def parse_resume_text(file_bytes: bytes, content_type: str) -> str:
    """Extract plain text from a PDF or DOCX resume."""
    if content_type == "application/pdf":
        return _parse_pdf(file_bytes)
    elif "wordprocessingml" in content_type:
        return _parse_docx(file_bytes)
    return ""


def _parse_pdf(file_bytes: bytes) -> str:
    if pdfplumber is None:
        return ""
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text_parts.append(extracted)
    return "\n".join(text_parts)


def _parse_docx(file_bytes: bytes) -> str:
    if Document is None:
        return ""
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


async def extract_style_snapshot(text: str) -> Optional[str]:
    """
    Extracts high-level writing style characteristics from the resume text.
    Cached on the Resume model to match tone during cover letter generation (BASIC/PRO).
    """
    if not text:
        return None

    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if len(s.strip()) > 10]
    words = re.findall(r"\b[A-Za-z]{3,}\b", text.lower())

    if not sentences or not words:
        return None

    avg_sentence_len = round(len(words) / len(sentences), 1)
    unique_ratio = round(len(set(words)) / len(words), 2)

    # Tone detection
    action_verbs = {
        "led", "built", "designed", "architected", "managed", "deployed",
        "optimized", "scaled", "automated", "created", "spearheaded", "developed"
    }
    action_count = sum(1 for w in words if w in action_verbs)
    action_density = round(action_count / len(words), 3)

    tone = "impactful" if action_density > 0.03 else "balanced"

    snapshot = {
        "avg_sentence_length": avg_sentence_len,
        "vocabulary_richness": unique_ratio,
        "action_verb_density": action_density,
        "primary_tone": tone,
    }
    return json.dumps(snapshot)
