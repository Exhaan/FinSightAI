"""
Financial Information Extraction (spec §9) + Data Traceability (spec §10) + Unit Scaling (spec §11).

Extracts structured financial metrics with:
- Metric name, standard label
- Value, fiscal year, unit scale
- Source page, document name, extraction method, confidence score
- Full context / row snippet for auditability
"""
import re
from dataclasses import dataclass, asdict

# Metric name -> list of regex patterns (case-insensitive)
METRIC_PATTERNS = {
    # Income Statement
    "Revenue": [
        r"total\s+revenue", r"net\s+revenue", r"total\s+net\s+sales",
        r"revenue\s+from\s+operations", r"^revenue$", r"\brevenues\b(?!\s*growth)",
    ],
    "Cost of Revenue": [
        r"cost\s+of\s+revenue", r"cost\s+of\s+goods\s+sold", r"cost\s+of\s+sales", r"\bcogs\b"
    ],
    "Gross Profit": [r"gross\s+profit", r"gross\s+margin\s+\$"],
    "Operating Expenses": [
        r"total\s+operating\s+expenses", r"operating\s+expenses", r"operating\s+costs"
    ],
    "Operating Income": [
        r"operating\s+income", r"income\s+from\s+operations", r"operating\s+profit",
        r"operating\s+earnings"
    ],
    "EBIT": [r"\bebit\b", r"earnings\s+before\s+interest\s+and\s+tax(?:es)?"],
    "EBITDA": [r"\bebitda\b", r"earnings\s+before\s+interest,\s+tax(?:es)?,?\s+depreciation"],
    "Interest Expense": [r"interest\s+expense", r"finance\s+costs"],
    "Tax Expense": [r"income\s+tax\s+expense", r"provision\s+for\s+income\s+taxes"],
    "Net Income": [
        r"net\s+income", r"net\s+profit", r"profit\s+for\s+the\s+year",
        r"net\s+earnings", r"net\s+income\s+attributable\s+to"
    ],
    "EPS": [r"diluted\s+earnings\s+per\s+share", r"basic\s+earnings\s+per\s+share", r"\beps\b"],

    # Balance Sheet
    "Cash and Cash Equivalents": [
        r"cash\s+and\s+cash\s+equivalents", r"cash\s+and\s+short[- ]term\s+investments",
        r"total\s+cash"
    ],
    "Current Assets": [r"total\s+current\s+assets", r"current\s+assets"],
    "Total Assets": [r"total\s+assets"],
    "Current Liabilities": [r"total\s+current\s+liabilities", r"current\s+liabilities"],
    "Total Debt": [
        r"total\s+debt", r"total\s+borrowings", r"short[- ]term\s+and\s+long[- ]term\s+debt",
        r"total\s+debt\s+and\s+finance\s+leases"
    ],
    "Short-Term Debt": [r"short[- ]term\s+debt", r"current\s+portion\s+of\s+long[- ]term\s+debt"],
    "Long-Term Debt": [r"long[- ]term\s+debt", r"non[- ]current\s+borrowings"],
    "Total Liabilities": [r"total\s+liabilities"],
    "Shareholders Equity": [
        r"total\s+shareholders.?\s+equity", r"total\s+stockholders.?\s+equity",
        r"shareholders.?\s+equity", r"total\s+equity"
    ],

    # Cash Flow Statement
    "Operating Cash Flow": [
        r"net\s+cash\s+(?:provided\s+by|from)\s+operating\s+activities",
        r"operating\s+cash\s+flow", r"cash\s+flow\s+from\s+operations",
        r"cash\s+generated\s+from\s+operations"
    ],
    "Capital Expenditure": [
        r"capital\s+expenditures?", r"purchases?\s+of\s+property.{0,40}equipment",
        r"additions\s+to\s+property,\s+plant\s+and\s+equipment", r"\bcapex\b",
    ],
    "Free Cash Flow": [r"free\s+cash\s+flow", r"\bfcf\b"],
    "Investing Cash Flow": [
        r"net\s+cash\s+(?:used\s+in|from)\s+investing\s+activities", r"investing\s+cash\s+flow"
    ],
    "Financing Cash Flow": [
        r"net\s+cash\s+(?:used\s+in|from)\s+financing\s+activities", r"financing\s+cash\s+flow"
    ],
}

NUMBER_RE = re.compile(
    r"\(?\$?\s*-?\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*\)?"
)

YEAR_HEADER_RE = re.compile(r"\b(20[1-3]\d)\b")

UNIT_SCALE_PATTERNS = [
    (r"in\s+billions", 1_000_000_000, "billions"),
    (r"in\s+millions", 1_000_000, "millions"),
    (r"in\s+thousands", 1_000, "thousands"),
    (r"in\s+lakhs?", 100_000, "lakhs"),
    (r"in\s+crores?", 10_000_000, "crores"),
]


@dataclass
class ExtractedValue:
    metric: str
    value: float
    year: int | None
    source_page: int
    document: str
    extraction_method: str   # "native_text" | "table"
    confidence: float
    raw_context: str
    unit_scale: str = "raw"


def detect_unit_scale(text: str) -> tuple[float, str]:
    """Detects unit scale in text/headers (in millions, in thousands, etc.)."""
    lower = text.lower()
    for pattern, multiplier, name in UNIT_SCALE_PATTERNS:
        if re.search(pattern, lower):
            return multiplier, name
    return 1.0, "raw"


def _parse_number(token: str) -> float | None:
    """Parses numeric string including negatives in brackets like (1,234.5)."""
    token = token.strip()
    if not token:
        return None
    negative = token.startswith("(") and token.endswith(")")
    cleaned = token.replace("(", "").replace(")", "").replace("$", "").replace(",", "").strip()
    if not cleaned:
        return None
    try:
        val = float(cleaned)
    except ValueError:
        return None
    return -val if negative else val


def _find_years_in_text(text: str) -> list[int]:
    """Finds all 4-digit years in text, sorted descending."""
    matches = YEAR_HEADER_RE.findall(text)
    years = sorted(list(set(int(y) for y in matches)), reverse=True)
    return years


def _extract_from_line(
    line: str,
    page_number: int,
    document: str,
    method: str,
    default_year: int | None,
    detected_years: list[int] | None = None,
    unit_scale: str = "raw",
) -> list[ExtractedValue]:
    results = []
    lower = line.lower()

    for metric, patterns in METRIC_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, lower):
                tokens = NUMBER_RE.findall(line)
                parsed_nums = []
                for tok in tokens:
                    val = _parse_number(tok)
                    # Filter out isolated single digits or years parsed accidentally as numbers
                    if val is not None and abs(val) > 0 and (abs(val) < 1900 or abs(val) > 2100 or "." in tok):
                        parsed_nums.append(val)
                    elif val == 0.0:
                        parsed_nums.append(val)

                if not parsed_nums:
                    continue

                confidence = 0.90 if method == "table" else 0.70

                # Multi-year column alignment
                years_to_use = detected_years if detected_years else ([default_year] if default_year else [2024])
                
                for idx, num in enumerate(parsed_nums):
                    col_year = years_to_use[idx] if idx < len(years_to_use) else (default_year or 2024)
                    results.append(ExtractedValue(
                        metric=metric,
                        value=num,
                        year=col_year,
                        source_page=page_number,
                        document=document,
                        extraction_method=method,
                        confidence=max(0.4, confidence - (0.05 * idx)),
                        raw_context=line.strip()[:300],
                        unit_scale=unit_scale,
                    ))
                break  # Matched this metric pattern
    return results


def extract_financial_metrics(
    pages: list[dict],
    tables_by_page: dict[int, str],
    document: str,
    default_year: int | None = None,
) -> list[ExtractedValue]:
    """
    Extracts all structured financial metrics across pages and tables.
    pages: list of page dicts from text_extractor.extract_text_per_page()
    tables_by_page: {page_number: flat_table_text}
    """
    all_results: list[ExtractedValue] = []

    # First pass: find global years mentioned across headers
    doc_years = []
    for p in pages:
        doc_years.extend(_find_years_in_text(p.get("text", "")))
    doc_years = sorted(list(set(doc_years)), reverse=True)
    if not doc_years and default_year:
        doc_years = [default_year]

    for page in pages:
        page_number = page["page_number"]
        page_text = page.get("text", "")
        _, unit_scale = detect_unit_scale(page_text)
        page_years = _find_years_in_text(page_text) or doc_years

        # Process table content first if present on page
        if page_number in tables_by_page:
            table_text = tables_by_page[page_number]
            for line in table_text.split("\n"):
                all_results.extend(
                    _extract_from_line(
                        line, page_number, document, "table", default_year, page_years, unit_scale
                    )
                )

        # Also process native page text for non-scanned pages
        if not page.get("likely_scanned", False):
            for line in page_text.split("\n"):
                all_results.extend(
                    _extract_from_line(
                        line, page_number, document, "native_text", default_year, page_years, unit_scale
                    )
                )

    return all_results


def dedupe_keep_highest_confidence(results: list[ExtractedValue]) -> list[ExtractedValue]:
    """
    Keeps the highest confidence hit per (metric, year).
    """
    best: dict[tuple, ExtractedValue] = {}
    for r in results:
        key = (r.metric, r.year)
        if key not in best or r.confidence > best[key].confidence:
            best[key] = r
    return list(best.values())


def to_dicts(results: list[ExtractedValue]) -> list[dict]:
    return [asdict(r) for r in results]
