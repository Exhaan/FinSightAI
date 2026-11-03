"""
Vision Module — Table Detection & Geometric Layout Engine (spec §4A & §5).

Extracts financial tables from both:
1. Bordered tables (standard grid lines)
2. Borderless tables (whitespace-separated columns, standard in Indian Ind AS annual reports)

Provides exact bounding box citations (x0, y0, x1, y1) in standard 72-DPI points
and pixel coordinates for visual UI overlay.
"""
import re
import unicodedata
import fitz  # PyMuPDF
from typing import List, Dict, Any, Optional, Tuple

# Indian Lakhs / Crores and standard numbers: e.g. 1,78,650 or 29,474 or (1,246) or 2.18
NUMERIC_TOKEN_RE = re.compile(r"\(?[\$₹`\xb7\ufffd\?]?\s*-?\d{1,3}(?:,\d{2,3})*(?:\.\d+)?\s*\)?")


def _is_numeric(text: str) -> bool:
    clean = re.sub(r"[^\d\.\-\(\)]", "", text).replace("(", "").replace(")", "").strip()
    try:
        float(clean)
        return True
    except ValueError:
        return False


def _clean_number(text: str) -> Optional[float]:
    t = text.strip()
    if not t:
        return None
    negative = t.startswith("(") and t.endswith(")")
    clean = re.sub(r"[^\d\.\-]", "", t).strip()
    try:
        val = float(clean)
        return -val if negative else val
    except ValueError:
        return None


class TableLayoutExtractor:
    """
    Detects financial statement rows, line-item labels, note numbers,
    and multi-year column values using geometric coordinate clustering.
    """

    def __init__(self, y_tolerance: float = 6.0):
        self.y_tolerance = y_tolerance

    def extract_rows_from_page(self, page: fitz.Page) -> List[Dict[str, Any]]:
        """
        Extracts structured financial rows with bounding boxes from a PyMuPDF page.
        """
        # Extract raw text blocks with bounding boxes: (x0, y0, x1, y1, text, block_no, type)
        blocks = page.get_text("blocks")
        rows = []

        # Also get words with fine-grained coordinates (x0, y0, x1, y1, word, block_no, line_no, word_no)
        words = page.get_text("words")
        if not words:
            try:
                tp = page.get_textpage_ocr(dpi=300, full=True)
                words = tp.extractWORDS()
            except Exception:
                words = []
        if not words:
            return []

        # Cluster words into horizontal lines by y-center
        lines_dict: Dict[int, List[Any]] = {}
        for w in words:
            # (x0, y0, x1, y1, word, block_no, line_no, word_no)
            norm_word = unicodedata.normalize('NFKD', str(w[4]))
            clean_w = (w[0], w[1], w[2], w[3], norm_word, w[5], w[6], w[7])
            y_center = (w[1] + w[3]) / 2.0
            # Cluster key
            cluster_key = int(y_center / self.y_tolerance) * self.y_tolerance
            if cluster_key not in lines_dict:
                lines_dict[cluster_key] = []
            lines_dict[cluster_key].append(clean_w)

        # Sort lines vertically from top to bottom
        sorted_keys = sorted(lines_dict.keys())

        for yk in sorted_keys:
            line_words = sorted(lines_dict[yk], key=lambda w: w[0])  # sort left-to-right
            if not line_words:
                continue

            line_text = " ".join(w[4] for w in line_words)
            x0 = min(w[0] for w in line_words)
            y0 = min(w[1] for w in line_words)
            x1 = max(w[2] for w in line_words)
            y1 = max(w[3] for w in line_words)

            # Analyze line structure: label, note reference, numeric values
            # Detect whether this line looks like a financial statement line
            numeric_words = [w for w in line_words if _is_numeric(w[4])]
            
            # Line must have text and at least one numeric word to be a statement row
            label_words = [w for w in line_words if not _is_numeric(w[4])]
            label_text = " ".join(w[4] for w in label_words).strip()

            parsed_values = []
            for nw in numeric_words:
                v = _clean_number(nw[4])
                if v is not None:
                    parsed_values.append({
                        "raw": nw[4],
                        "value": v,
                        "bbox": (round(nw[0], 1), round(nw[1], 1), round(nw[2], 1), round(nw[3], 1)),
                    })

            rows.append({
                "line_text": line_text,
                "label": label_text,
                "bbox": (round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1)),
                "numeric_values": parsed_values,
                "is_financial_row": len(label_text) > 2 and len(parsed_values) >= 1,
            })

        return rows

    def extract_statement_table(
        self,
        pdf_path: str,
        page_number: int,
        default_years: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Extracts a complete structured table from a statement page.
        """
        doc = fitz.open(pdf_path)
        page = doc[page_number - 1]
        rows = self.extract_rows_from_page(page)
        
        # Detect year headers on this page
        raw_text = page.get_text("text") or ""
        text = unicodedata.normalize('NFKD', raw_text)
        year_matches = re.findall(r"\b(20[1-3]\d)\b", text)
        page_years = sorted(list(set(int(y) for y in year_matches)), reverse=True)
        effective_years = page_years if page_years else (default_years or [2024, 2023])

        # Filter down to financial rows
        statement_rows = [r for r in rows if r["is_financial_row"]]

        doc.close()
        return {
            "page_number": page_number,
            "years": effective_years,
            "total_rows_found": len(rows),
            "financial_rows": statement_rows,
        }
