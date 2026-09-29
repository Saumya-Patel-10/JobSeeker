import io
from typing import List

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from docx import Document
except ImportError:
    Document = None


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extracts text from a PDF file."""
    if pdfplumber is None:
        return ""
    content = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                content.append(extracted)
    return "\n".join(content)


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extracts text from a DOCX file."""
    if Document is None:
        return ""
    doc = Document(io.BytesIO(file_bytes))
    content = [para.text for para in doc.paragraphs if para.text.strip()]
    return "\n".join(content)


def extract_text(file_bytes: bytes, extension: str) -> str:
    """Helper to decide which extraction method to use."""
    if extension.lower() == ".pdf":
        return extract_text_from_pdf(file_bytes)
    elif extension.lower() == ".docx":
        return extract_text_from_docx(file_bytes)
    else:
        raise ValueError(f"Unsupported file extension: {extension}")
