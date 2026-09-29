"""
Resume Parser Service
- Extracts plain text from PDF (pdfplumber) and DOCX (python-docx)
- Extracts style snapshot: tone, avg sentence length, vocabulary richness
"""
import io
import json
import re
from typing import Optional

import pdfplumber
from docx import Document


async def parse_resume_text(file_bytes: bytes, content_type: str) -> str:
    """Extract plain text from a PDF or DOCX resume."""
    if content_type == "application/pdf":
        return _parse_pdf(file_bytes)
    elif "wordprocessingml" in content_type:
        return _parse_docx(file_bytes)
    return ""


def _parse_pdf(file_bytes: bytes) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text_parts.append(extracted)
    return "\n".join(text_parts)


def _parse_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


async def extract_style_snapshot(text: str) -> Optional[str]:
    """
    Analyse writing style for cover letter matching.
    Returns a JSON string with:
      - avg_words_per_sentence
      - formality_score (estimated)
      - common_phrases (top 5)
    """
    if not text or len(text) < 100:
        return None

    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

    if not sentences:
        return None

    avg_words = sum(len(s.split()) for s in sentences) / len(sentences)

    # Very simple formality heuristic — ratio of formal words
    formal_words = {"leverage", "spearheaded", "optimized", "managed", "led",
                    "developed", "implemented", "collaborated", "strategic", "delivered"}
    all_words = set(text.lower().split())
    formality_score = len(formal_words & all_words) / max(len(all_words), 1)

    # Top 3-word phrases
    words = re.findall(r"\b[a-z]{4,}\b", text.lower())
    phrase_counts: dict[str, int] = {}
    for i in range(len(words) - 2):
        phrase = f"{words[i]} {words[i+1]} {words[i+2]}"
        phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1

    top_phrases = sorted(phrase_counts, key=phrase_counts.get, reverse=True)[:5]

    snapshot = {
        "avg_words_per_sentence": round(avg_words, 1),
        "formality_score": round(formality_score, 3),
        "common_phrases": top_phrases,
        "sample_sentences": sentences[:3],
    }
    return json.dumps(snapshot)
