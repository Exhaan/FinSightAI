"""
Module 2 (spec §6) — PDF loading + basic validation.

Responsibility: open a PDF, validate it, report page count, and hand back
a PyMuPDF document object for downstream modules to use.
"""
import os
import fitz  # PyMuPDF


class PDFLoadError(Exception):
    pass


def validate_pdf(filepath: str, max_size_mb: int = 100) -> None:
    if not os.path.exists(filepath):
        raise PDFLoadError(f"File not found: {filepath}")
    if not filepath.lower().endswith(".pdf"):
        raise PDFLoadError("Only .pdf files are supported in the MVP.")
    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    if size_mb > max_size_mb:
        raise PDFLoadError(f"File too large ({size_mb:.1f} MB > {max_size_mb} MB limit).")


def load_pdf(filepath: str) -> fitz.Document:
    """Validate and open a PDF, returning the PyMuPDF Document."""
    validate_pdf(filepath)
    try:
        doc = fitz.open(filepath)
    except Exception as e:
        raise PDFLoadError(f"Could not open PDF: {e}")
    if doc.page_count == 0:
        raise PDFLoadError("PDF has zero pages.")
    return doc


def pdf_summary(filepath: str) -> dict:
    """Quick metadata summary used by the /upload endpoint response."""
    doc = load_pdf(filepath)
    summary = {
        "filename": os.path.basename(filepath),
        "num_pages": doc.page_count,
        "metadata": doc.metadata,
    }
    doc.close()
    return summary
