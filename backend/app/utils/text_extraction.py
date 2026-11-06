import io
from bs4 import BeautifulSoup
import pdfplumber
from docx import Document

def strip_html(html: str) -> str:
    """Strip HTML tags from a string and return plain text."""
    return BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)

def extract_text_from_pdf(file_bytes: bytes) -> str:
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text(filename: str, content_type: str, file_bytes: bytes) -> str:
    if content_type == "application/pdf" or filename.lower().endswith(".pdf"):
        text = extract_text_from_pdf(file_bytes)
    elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or filename.lower().endswith(".docx"):
        text = extract_text_from_docx(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {content_type}")
        
    # Cap text length to ~50k chars to protect DB/LLM from huge inputs
    if len(text) > 50000:
        text = text[:50000]
        
    return text
