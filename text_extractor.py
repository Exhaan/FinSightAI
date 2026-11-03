"""
Native text extraction (spec §6 steps 3-4).

Strategy (spec §7 "preferred logic"): try native PDF text extraction first.
A page is flagged as "likely_scanned" when it yields almost no text — that's
the signal Phase 1b's OCR module should pick it up instead.
"""
import fitz
from document_processing.pdf_loader import load_pdf

MIN_CHARS_FOR_NATIVE_TEXT = 20  # below this, treat page as image-only


def extract_text_per_page(filepath: str) -> list[dict]:
    """
    Returns a list of dicts, one per page:
        {
          "page_number": int (1-indexed),
          "text": str,
          "char_count": int,
          "likely_scanned": bool,
        }
    """
    doc = load_pdf(filepath)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text") or ""
        char_count = len(text.strip())
        pages.append({
            "page_number": i + 1,
            "text": text,
            "char_count": char_count,
            "likely_scanned": char_count < MIN_CHARS_FOR_NATIVE_TEXT,
        })
    doc.close()
    return pages


def full_text(filepath: str) -> str:
    """Convenience: whole-document text, pages joined with a page-break marker."""
    pages = extract_text_per_page(filepath)
    return "\n\n".join(f"--- PAGE {p['page_number']} ---\n{p['text']}" for p in pages)
