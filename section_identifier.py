"""
Document Structure Recognition / Section Identifier (spec §8).

Identifies and classifies pages/sections within corporate financial reports:
- Business Overview
- Management's Discussion and Analysis (MD&A)
- Consolidated Statements of Operations (Income Statement)
- Consolidated Balance Sheets
- Consolidated Statements of Cash Flows
- Risk Factors
- Notes to Financial Statements
- ESG / Sustainability Disclosures
- Corporate Governance
"""
import re

SECTION_PATTERNS = {
    "Income Statement": [
        r"statements?\s+of\s+operations",
        r"income\s+statements?",
        r"statements?\s+of\s+(?:earnings|profit\s+and\s+loss)",
        r"consolidated\s+statements?\s+of\s+income",
    ],
    "Balance Sheet": [
        r"balance\s+sheets?",
        r"statements?\s+of\s+financial\s+position",
        r"consolidated\s+balance\s+sheets?",
    ],
    "Cash Flow Statement": [
        r"statements?\s+of\s+cash\s+flows?",
        r"cash\s+flow\s+statements?",
        r"consolidated\s+statements?\s+of\s+cash\s+flows?",
    ],
    "MD&A": [
        r"management.?s\s+discussion\s+and\s+analysis",
        r"\bmd&a\b",
        r"financial\s+review\s+and\s+analysis",
    ],
    "Business Overview": [
        r"business\s+overview",
        r"item\s+1\.?\s+business",
        r"company\s+overview",
        r"about\s+the\s+company",
    ],
    "Risk Factors": [
        r"risk\s+factors",
        r"item\s+1a\.?\s+risk\s+factors",
        r"principal\s+risks",
    ],
    "ESG / Sustainability": [
        r"environmental,\s+social\s+(?:and|&)\s+governance",
        r"sustainability\s+report",
        r"esg\s+(?:disclosures|performance|metrics)",
        r"corporate\s+responsibility",
    ],
    "Notes to Financial Statements": [
        r"notes\s+to\s+(?:consolidated\s+)?financial\s+statements",
        r"accompanying\s+notes",
    ],
    "Corporate Governance": [
        r"corporate\s+governance",
        r"board\s+of\s+directors",
        r"executive\s+compensation",
    ]
}


def classify_page_section(text: str, page_number: int) -> dict:
    """
    Analyzes page text to classify the primary section type and detected section tags.
    """
    lower = text.lower()
    matched_sections = []

    for section_name, patterns in SECTION_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, lower):
                matched_sections.append(section_name)
                break

    primary_section = matched_sections[0] if matched_sections else "General Information"

    return {
        "page_number": page_number,
        "primary_section": primary_section,
        "matched_sections": matched_sections,
        "is_financial_statement": primary_section in [
            "Income Statement", "Balance Sheet", "Cash Flow Statement"
        ]
    }


def classify_document_sections(pages: list[dict]) -> list[dict]:
    """
    Classifies all pages in a document.
    pages: list of dicts from text_extractor.extract_text_per_page().
    """
    classified = []
    for page in pages:
        res = classify_page_section(page.get("text", ""), page["page_number"])
        classified.append({
            **page,
            **res
        })
    return classified
