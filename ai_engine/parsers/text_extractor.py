import pdfplumber
from docx import Document
from typing import List
import io

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extracts text from a PDF file."""
    content = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            content.append(page.extract_text())
    return "\n".join(content)

def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extracts text from a DOCX file."""
    doc = Document(io.BytesIO(file_bytes))
    content = [para.text for para in doc.paragraphs]
    return "\n".join(content)

def extract_text(file_bytes: bytes, extension: str) -> str:
    """Helper to decide which extraction method to use."""
    if extension.lower() == ".pdf":
        return extract_text_from_pdf(file_bytes)
    elif extension.lower() == ".docx":
        return extract_text_from_docx(file_bytes)
    else:
        raise ValueError(f"Unsupported file extension: {extension}")
