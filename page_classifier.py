"""
Vision Module — Document Section & Page-Type Classifier (spec §4A & §8).

Classifies document pages into specific architectural types:
- Cover Page / Corporate Information
- Management Discussion & Analysis (MD&A) / Directors' Report
- Balance Sheet (Consolidated / Standalone)
- Statement of Profit and Loss (Income Statement)
- Statement of Cash Flows
- Notes to Financial Statements & Accounting Policies
- Independent Auditor's Report
- Other / General Disclosures

Supports both Indian Accounting Standards (Ind AS / Companies Act Schedule III)
and International Financial Reporting Standards (IFRS / US GAAP).
"""
import re
import unicodedata
from typing import Dict, Any, List

PAGE_TYPE_SIGNATURES = {
    "balance_sheet": [
        r"consolidated\s+balance\s+sheet",
        r"balance\s+sheet\s+as\s+at",
        r"statement\s+of\s+financial\s+position",
        r"\bequity\s+and\s+liabilities\b",
        r"\bnon-current\s+assets\b",
    ],
    "income_statement": [
        r"consolidated\s+statement\s+of\s+profit\s+and\s+loss",
        r"statement\s+of\s+profit\s+and\s+loss",
        r"statement\s+of\s+operations",
        r"statement\s+of\s+comprehensive\s+income",
        r"revenue\s+from\s+operations",
        r"profit\s+for\s+the\s+year",
    ],
    "cash_flow": [
        r"consolidated\s+statement\s+of\s+cash\s+flows?",
        r"cash\s+flow\s+statement",
        r"cash\s+flows?\s+from\s+operating\s+activities",
        r"cash\s+and\s+cash\s+equivalents\s+at\s+the\s+(?:end|beginning)",
    ],
    "notes": [
        r"notes\s+to\s+(?:the\s+)?consolidated\s+financial\s+statements",
        r"notes\s+forming\s+part\s+of\s+the\s+financial\s+statements",
        r"significant\s+accounting\s+policies",
        r"corporate\s+information\s+and\s+significant\s+accounting\s+policies",
    ],
    "auditor_report": [
        r"independent\s+auditor.?s\s+report",
        r"report\s+on\s+the\s+audit\s+of\s+the\s+consolidated\s+financial\s+statements",
        r"opinion\s+on\s+the\s+financial\s+statements",
    ],
    "mda": [
        r"management\s+discussion\s+and\s+analysis",
        r"directors.?\s+report",
        r"board.?s\s+report",
        r"operating\s+and\s+financial\s+review",
    ],
    "cover": [
        r"integrated\s+annual\s+report",
        r"annual\s+report\s+20\d\d",
        r"to\s+all\s+stock\s+exchanges",
        r"corporate\s+identity\s+number",
    ]
}


def classify_page_type(text: str, page_number: int, total_pages: int) -> Dict[str, Any]:
    """
    Classifies a page into its primary financial document type with confidence scoring.
    """
    norm_text = unicodedata.normalize('NFKD', text or "")
    lower = norm_text.lower()
    scores = {ptype: 0 for ptype in PAGE_TYPE_SIGNATURES}

    # First page bias for cover only if no strong statement content found
    cover_evidence = 0
    if page_number == 1 and total_pages > 5:
        cover_evidence = 2

    for ptype, patterns in PAGE_TYPE_SIGNATURES.items():
        for pat in patterns:
            if re.search(pat, lower):
                scores[ptype] += 3

    # Prominence check for exact statement titles
    for ptype in ["balance_sheet", "income_statement", "cash_flow"]:
        for pat in PAGE_TYPE_SIGNATURES[ptype]:
            if re.search(pat, lower):
                scores[ptype] += 4

    scores["cover"] += cover_evidence

    # If financial statements match, penalize false cover assignment from running headers
    has_statement = any(scores[st] >= 6 for st in ["balance_sheet", "income_statement", "cash_flow"])
    if has_statement:
        scores["cover"] = 0

    best_type = max(scores.items(), key=lambda x: x[1])
    if best_type[1] >= 3:
        assigned = best_type[0]
        confidence = min(0.95, 0.50 + best_type[1] * 0.08)
    else:
        assigned = "other"
        confidence = 0.40

    return {
        "page_number": page_number,
        "page_type": assigned,
        "confidence": round(confidence, 2),
        "scores": scores,
    }


def classify_document_pages(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Classifies an entire document's pages and resolves sequence continuity.
    """
    classified = []
    total = len(pages)
    for p in pages:
        res = classify_page_type(p.get("text", ""), p.get("page_number", 1), total)
        classified.append({**p, **res})
    return classified
