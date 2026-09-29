"""
AI Service — all GPT-4o calls:
  - score_match         : cosine-style keyword matching + LLM score (0.0-1.0)
  - tailor_resume       : rewrite resume sections to match job description
  - generate_cover_letter: write cover letter matching user's writing style
  - ats_optimize_resume : inject ATS keywords, formatting rules (PRO)
  - generate_interview_questions : predict likely interview questions (PRO)
"""
import json
import io
from typing import Optional

try:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY or "dummy-key")
except Exception:
    AsyncOpenAI = None
    client = None

from tenacity import retry, stop_after_attempt, wait_exponential

try:
    from docx import Document
except ImportError:
    Document = None


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def score_match(resume_text: str, job_description: str) -> float:
    """
    Use GPT-4o to score how well the resume matches the job.
    Returns a float between 0.0 and 1.0.
    """
    prompt = f"""
You are an expert recruiter. Analyse the candidate's resume against the job description.
Return ONLY a JSON object with one key: "score" (float 0.0 to 1.0).
0.0 = no match, 1.0 = perfect match.

RESUME:
{resume_text[:4000]}

JOB DESCRIPTION:
{job_description[:3000]}
"""
    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=64,
    )
    data = json.loads(response.choices[0].message.content)
    return float(data.get("score", 0.0))


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def tailor_resume(
    resume_text: str,
    job_description: str,
    job_title: str,
    company: str,
) -> bytes:
    """
    GPT-4o rewrites the resume to highlight relevant experience for the job.
    Returns DOCX bytes.
    """
    prompt = f"""
You are an expert resume writer. Rewrite the provided resume to be perfectly tailored
for the following job. Keep the same structure and facts — only adjust language, emphasis,
bullet points and keywords to match the job requirements.

JOB TITLE: {job_title}
COMPANY: {company}
JOB DESCRIPTION:
{job_description[:3000]}

ORIGINAL RESUME:
{resume_text[:4000]}

Return the tailored resume as plain text using the same section structure.
Use "##" as section headers (e.g., ## Experience, ## Skills).
"""
    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=2000,
    )
    tailored_text = response.choices[0].message.content
    return _text_to_docx(tailored_text, f"Tailored Resume — {job_title} @ {company}")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def generate_cover_letter(
    resume_text: str,
    job_description: str,
    job_title: str,
    company: str,
    style_snapshot: Optional[str] = None,
) -> bytes:
    """
    BASIC + PRO: Generate a cover letter matching the user's writing style.
    Returns DOCX bytes.
    """
    style_context = ""
    if style_snapshot:
        style_context = f"\nMATCH this writing style (tone, vocabulary, sentence length):\n{style_snapshot}\n"

    prompt = f"""
You are a professional cover letter writer.
Write a compelling, personalized cover letter for this job application.
{style_context}

JOB TITLE: {job_title}
COMPANY: {company}
JOB DESCRIPTION:
{job_description[:2000]}

CANDIDATE'S RESUME SUMMARY:
{resume_text[:2000]}

Write a professional 3-4 paragraph cover letter.
"""
    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=800,
    )
    cl_text = response.choices[0].message.content
    return _text_to_docx(cl_text, f"Cover Letter — {job_title} @ {company}")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def ats_optimize_resume(resume_docx_bytes: bytes, job_description: str) -> bytes:
    """
    PRO plan: Optimize resume to bypass ATS systems.
    - Injects keywords from job description
    - Removes tables/graphics that confuse ATS parsers
    - Uses standard section headings
    Returns optimized DOCX bytes.
    """
    # Extract current text
    doc = Document(io.BytesIO(resume_docx_bytes))
    current_text = "\n".join([p.text for p in doc.paragraphs])

    prompt = f"""
You are an ATS (Applicant Tracking System) expert.
Optimize this resume to achieve maximum ATS score for the job below.
Rules:
1. Include verbatim keywords from the job description naturally in context.
2. Use standard section headers: Summary, Experience, Education, Skills, Certifications.
3. Remove any special characters or symbols that ATS systems cannot parse.
4. Keep all factual content accurate — never fabricate experience.
5. Format skills as a comma-separated list.

JOB DESCRIPTION:
{job_description[:2500]}

CURRENT RESUME:
{current_text[:3500]}

Return the ATS-optimized resume as plain text with ## section headers.
"""
    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=2000,
    )
    optimized_text = response.choices[0].message.content
    return _text_to_docx(optimized_text, "ATS-Optimized Resume")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def generate_interview_questions(
    job_description: str,
    resume_text: str,
) -> list[dict]:
    """
    PRO plan: Predict likely interview questions with guidance.
    Returns a list of {"question": ..., "guidance": ...} dicts.
    """
    prompt = f"""
You are an expert career coach and technical interviewer.
Based on the job description and candidate resume, predict the 10 most likely
interview questions and provide a short guidance tip for each.

JOB DESCRIPTION:
{job_description[:2000]}

CANDIDATE RESUME:
{resume_text[:2000]}

Return ONLY a JSON array of objects with keys "question" and "guidance".
"""
    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.5,
        max_tokens=1200,
    )
    data = json.loads(response.choices[0].message.content)
    return data.get("questions", data)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _text_to_docx(text: str, title: str) -> bytes:
    """Convert plain text (with ## headers) to a DOCX file bytes."""
    doc = Document()
    doc.add_heading(title, level=0)
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("## "):
            doc.add_heading(stripped[3:], level=1)
        elif stripped.startswith("# "):
            doc.add_heading(stripped[2:], level=2)
        elif stripped.startswith("- ") or stripped.startswith("• "):
            doc.add_paragraph(stripped[2:], style="List Bullet")
        elif stripped:
            doc.add_paragraph(stripped)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
