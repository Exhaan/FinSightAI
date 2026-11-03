"""
Table extraction (spec §6 step 8, §7).

MVP uses pdfplumber only (no Camelot) — see PROJECT_CONTEXT.md §2 for why.
"""
import pdfplumber


def extract_tables_per_page(filepath: str) -> list[dict]:
    """
    Returns a list of dicts, one per page that has at least one table:
        {
          "page_number": int (1-indexed),
          "tables": [ [[cell, cell, ...], ...], ... ]   # list of tables, each a list of rows
        }
    """
    results = []
    with pdfplumber.open(filepath) as pdf:
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            if tables:
                results.append({
                    "page_number": i + 1,
                    "tables": tables,
                })
    return results


def tables_to_flat_text(tables_on_page: list) -> str:
    """
    Flattens a page's tables into pipe-separated text lines so the same
    regex-based financial_extractor can scan table content alongside
    normal paragraph text (a row like "Revenue | 45,000 | 41,200" is easy
    to pattern-match).
    """
    lines = []
    for table in tables_on_page:
        for row in table:
            cells = [str(c) if c is not None else "" for c in row]
            lines.append(" | ".join(cells))
    return "\n".join(lines)
