"""PDF text extraction utility.
Lightweight: pdfminer for text PDFs, pytesseract for image-only PDFs, camelot for tables.
"""
from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Tuple

from pdfminer.high_level import extract_text  # type: ignore
from pdfminer.pdfparser import PDFSyntaxError  # type: ignore

try:
    import camelot  # type: ignore
except ImportError:  # pragma: no cover
    camelot = None  # type: ignore

try:
    from pdf2image import convert_from_path  # type: ignore
    import pytesseract  # type: ignore
except ImportError:  # pragma: no cover
    convert_from_path = pytesseract = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class ExtractionError(RuntimeError):
    """Raised when PDF text cannot be extracted."""


def extract(pdf_path: Path | str | bytes) -> Tuple[str, list]:
    """Return raw text and list of camelot Table objects (optional)."""
    # pdfminer expects path or bytes
    try:
        if isinstance(pdf_path, (str, Path)):
            raw_text: str = extract_text(pdf_path)
        else:
            raw_text = extract_text(io.BytesIO(pdf_path))
    except (PDFSyntaxError, AttributeError):  # corrupted or encrypted
        raw_text = ""

    tables = []
    if camelot is not None:
        try:
            # flavor="stream" works for most invoices
            tables = camelot.read_pdf(str(pdf_path), pages="all", flavor="stream")  # type: ignore[arg-type]
        except Exception:  # pragma: no cover
            tables = []

    # Fallback to OCR if text empty
    if not raw_text.strip() and convert_from_path and pytesseract:
        try:
            images = convert_from_path(pdf_path if isinstance(pdf_path, (str, Path)) else None)  # type: ignore[arg-type]
            ocr_pages = [pytesseract.image_to_string(img) for img in images]
            raw_text = "\n".join(ocr_pages)
        except Exception as exc:  # pragma: no cover
            LOGGER.error("OCR extraction failed: %s", exc)

    if not raw_text.strip():
        raise ExtractionError("Unable to extract text from PDF")

    return raw_text, tables
