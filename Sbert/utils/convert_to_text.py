import os
from pdfminer.high_level import extract_text as extract_pdf_text
from docx import Document

def convert_to_text(file_path):
    """
    Converts a document file (PDF, DOCX, or TXT) to plain text.

    Args:
        file_path (str): Path to the document file.

    Returns:
        str: Extracted plain text from the document.

    Raises:
        ValueError: If the file extension is unsupported.
    """
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext == ".pdf":
        return extract_pdf_text(file_path)

    elif ext == ".docx":
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    else:
        raise ValueError(f"Unsupported file type: {ext}. Supported formats are PDF, DOCX, and TXT.")
