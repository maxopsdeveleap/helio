"""
Document parsing utilities for PDF and DOCX files.
Extracts raw text from documents for further processing.
"""
import logging
from pathlib import Path
from typing import Optional

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None

logger = logging.getLogger(__name__)


def parse_pdf(file_path: Path) -> str:
    """
    Extract text from a PDF file.

    Args:
        file_path: Path to the PDF file

    Returns:
        Extracted text as a single string

    Raises:
        ImportError: If PyPDF2 is not installed
        Exception: If PDF parsing fails
    """
    if PdfReader is None:
        raise ImportError("PyPDF2 is not installed. Install with: pip install pypdf2")

    try:
        reader = PdfReader(str(file_path))
        text_parts = []

        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)

        full_text = "\n\n".join(text_parts)
        logger.info(f"Extracted {len(full_text)} characters from PDF: {file_path.name}")
        return full_text

    except Exception as e:
        logger.error(f"Failed to parse PDF {file_path}: {e}")
        raise


def parse_docx(file_path: Path) -> str:
    """
    Extract text from a DOCX file.

    Args:
        file_path: Path to the DOCX file

    Returns:
        Extracted text as a single string

    Raises:
        ImportError: If python-docx is not installed
        Exception: If DOCX parsing fails
    """
    if Document is None:
        raise ImportError("python-docx is not installed. Install with: pip install python-docx")

    try:
        doc = Document(str(file_path))
        text_parts = []

        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)

        full_text = "\n".join(text_parts)
        logger.info(f"Extracted {len(full_text)} characters from DOCX: {file_path.name}")
        return full_text

    except Exception as e:
        logger.error(f"Failed to parse DOCX {file_path}: {e}")
        raise


def parse_document(file_path: Path) -> str:
    """
    Parse a document (PDF or DOCX) and extract text.

    Args:
        file_path: Path to the document

    Returns:
        Extracted text as a single string

    Raises:
        ValueError: If file format is not supported
        Exception: If parsing fails
    """
    suffix = file_path.suffix.lower()

    if suffix == '.pdf':
        return parse_pdf(file_path)
    elif suffix in ['.docx', '.doc']:
        # Note: .doc files (old Word format) are not supported by python-docx
        # Only .docx files will work
        if suffix == '.doc':
            logger.warning(f"Old .doc format may not be supported. Consider converting to .docx: {file_path.name}")
        return parse_docx(file_path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Supported formats: .pdf, .docx")
