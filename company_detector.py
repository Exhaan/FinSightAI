"""
Company & Ticker Entity Detector — Automated Identification of Corporate Filings.
Detects company name, ticker, sector, industry, exchange, currency, and valuation defaults
from uploaded PDF filenames and page text (supporting both Indian BSE/NSE and Global US SEC filings).
"""
import os
import re
import unicodedata
from typing import Dict, Any, Optional
import fitz

KNOWN_PROFILES = [
    {
        "keywords": ["nvidia", "nvda"],
        "name": "NVIDIA Corporation",
        "ticker": "NVDA",
        "sector": "Technology",
        "industry": "Semiconductors & AI Hardware",
        "exchange": "NASDAQ",
        "currency": "$",
        "currency_symbol": "$",
        "unit_label": "$ Millions",
        "unit_div": 1_000_000.0,
        "is_indian": False,
        "rf": 0.040,
        "tax_rate": 0.16,
        "terminal_growth": 0.025,
        "terminal_roic": 0.35,
        "default_long_run_margin": 0.48,
        "default_beta": 1.45,
        "default_pe": 48.0,
    },
    {
        "keywords": ["apple", "aapl"],
        "name": "Apple Inc.",
        "ticker": "AAPL",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "exchange": "NASDAQ",
        "currency": "$",
        "currency_symbol": "$",
        "unit_label": "$ Millions",
        "unit_div": 1_000_000.0,
        "is_indian": False,
        "rf": 0.040,
        "tax_rate": 0.16,
        "terminal_growth": 0.025,
        "terminal_roic": 0.35,
        "default_long_run_margin": 0.31,
        "default_beta": 1.05,
        "default_pe": 33.5,
    },
    {
        "keywords": ["tesla", "tsla"],
        "name": "Tesla Inc.",
        "ticker": "TSLA",
        "sector": "Consumer Cyclical",
        "industry": "Auto Manufacturers & Clean Energy",
        "exchange": "NASDAQ",
        "currency": "$",
        "currency_symbol": "$",
        "unit_label": "$ Millions",
        "unit_div": 1_000_000.0,
        "is_indian": False,
        "rf": 0.040,
        "tax_rate": 0.18,
        "terminal_growth": 0.030,
        "terminal_roic": 0.20,
        "default_long_run_margin": 0.15,
        "default_beta": 1.55,
        "default_pe": 62.0,
    },
    {
        "keywords": ["amazon", "amzn"],
        "name": "Amazon.com Inc.",
        "ticker": "AMZN",
        "sector": "Consumer Cyclical",
        "industry": "Internet Retail & Cloud (AWS)",
        "exchange": "NASDAQ",
        "currency": "$",
        "currency_symbol": "$",
        "unit_label": "$ Millions",
        "unit_div": 1_000_000.0,
        "is_indian": False,
        "rf": 0.040,
        "tax_rate": 0.19,
        "terminal_growth": 0.030,
        "terminal_roic": 0.20,
        "default_long_run_margin": 0.12,
        "default_beta": 1.15,
        "default_pe": 41.0,
    },
    {
        "keywords": ["microsoft", "msft"],
        "name": "Microsoft Corporation",
        "ticker": "MSFT",
        "sector": "Technology",
        "industry": "Software & Cloud Services",
        "exchange": "NASDAQ",
        "currency": "$",
        "currency_symbol": "$",
        "unit_label": "$ Millions",
        "unit_div": 1_000_000.0,
        "is_indian": False,
        "rf": 0.040,
        "tax_rate": 0.18,
        "terminal_growth": 0.025,
        "terminal_roic": 0.32,
        "default_long_run_margin": 0.42,
        "default_beta": 1.10,
        "default_pe": 34.0,
    },
    {
        "keywords": ["johnson & johnson", "johnson and johnson", "jnj"],
        "name": "Johnson & Johnson",
        "ticker": "JNJ",
        "sector": "Healthcare",
        "industry": "Drug Manufacturers — General",
        "exchange": "NYSE",
        "currency": "$",
        "currency_symbol": "$",
        "unit_label": "$ Millions",
        "unit_div": 1_000_000.0,
        "is_indian": False,
        "rf": 0.040,
        "tax_rate": 0.17,
        "terminal_growth": 0.025,
        "terminal_roic": 0.22,
        "default_long_run_margin": 0.26,
        "default_beta": 0.65,
        "default_pe": 24.0,
    },
    {
        "keywords": ["pfizer", "pfe"],
        "name": "Pfizer Inc.",
        "ticker": "PFE",
        "sector": "Healthcare",
        "industry": "Drug Manufacturers — General",
        "exchange": "NYSE",
        "currency": "$",
        "currency_symbol": "$",
        "unit_label": "$ Millions",
        "unit_div": 1_000_000.0,
        "is_indian": False,
        "rf": 0.040,
        "tax_rate": 0.16,
        "terminal_growth": 0.025,
        "terminal_roic": 0.18,
        "default_long_run_margin": 0.24,
        "default_beta": 0.70,
        "default_pe": 16.5,
    },
    {
        "keywords": ["nextera", "nee"],
        "name": "NextEra Energy, Inc.",
        "ticker": "NEE",
        "sector": "Utilities",
        "industry": "Renewable Electricity & Utilities",
        "exchange": "NYSE",
        "currency": "$",
        "currency_symbol": "$",
        "unit_label": "$ Millions",
        "unit_div": 1_000_000.0,
        "is_indian": False,
        "rf": 0.040,
        "tax_rate": 0.18,
        "terminal_growth": 0.025,
        "terminal_roic": 0.12,
        "default_long_run_margin": 0.28,
        "default_beta": 0.60,
        "default_pe": 22.0,
    },
    {
        "keywords": ["united spirits", "diageo", "mcdowell", "unitdspr", "532432"],
        "name": "United Spirits Limited",
        "ticker": "MCDOWELL-N",
        "sector": "Consumer Defensive",
        "industry": "Beverages — Wineries & Distilleries",
        "exchange": "NSE / BSE",
        "currency": "₹",
        "currency_symbol": "₹",
        "unit_label": "₹ Crores",
        "unit_div": 10_000_000.0,
        "is_indian": True,
        "rf": 0.071,
        "tax_rate": 0.25,
        "terminal_growth": 0.045,
        "terminal_roic": 0.28,
        "default_long_run_margin": 0.18,
        "default_beta": 0.75,
        "default_pe": 62.0,
    },
    {
        "keywords": ["united breweries", "ubl", "heineken", "532478"],
        "name": "United Breweries Limited",
        "ticker": "UBL",
        "sector": "Consumer Defensive",
        "industry": "Beverages — Brewers",
        "exchange": "NSE / BSE",
        "currency": "₹",
        "currency_symbol": "₹",
        "unit_label": "₹ Crores",
        "unit_div": 10_000_000.0,
        "is_indian": True,
        "rf": 0.071,
        "tax_rate": 0.25,
        "terminal_growth": 0.045,
        "terminal_roic": 0.20,
        "default_long_run_margin": 0.14,
        "default_beta": 0.80,
        "default_pe": 55.0,
    },
    {
        "keywords": ["radico khaitan", "radico", "532497"],
        "name": "Radico Khaitan Limited",
        "ticker": "RADICO",
        "sector": "Consumer Defensive",
        "industry": "Beverages — Wineries & Distilleries",
        "exchange": "NSE / BSE",
        "currency": "₹",
        "currency_symbol": "₹",
        "unit_label": "₹ Crores",
        "unit_div": 10_000_000.0,
        "is_indian": True,
        "rf": 0.071,
        "tax_rate": 0.25,
        "terminal_growth": 0.050,
        "terminal_roic": 0.22,
        "default_long_run_margin": 0.15,
        "default_beta": 0.85,
        "default_pe": 48.0,
    },
    {
        "keywords": ["infosys", "infy"],
        "name": "Infosys Limited",
        "ticker": "INFY",
        "sector": "Information Technology",
        "industry": "IT Consulting & Software",
        "exchange": "NSE / BSE",
        "currency": "₹",
        "currency_symbol": "₹",
        "unit_label": "₹ Crores",
        "unit_div": 10_000_000.0,
        "is_indian": True,
        "rf": 0.071,
        "tax_rate": 0.25,
        "terminal_growth": 0.045,
        "terminal_roic": 0.25,
        "default_long_run_margin": 0.23,
        "default_beta": 0.85,
        "default_pe": 24.5,
    },
    {
        "keywords": ["tcs", "tata consultancy"],
        "name": "Tata Consultancy Services Limited",
        "ticker": "TCS",
        "sector": "Information Technology",
        "industry": "IT Services & Consulting",
        "exchange": "NSE / BSE",
        "currency": "₹",
        "currency_symbol": "₹",
        "unit_label": "₹ Crores",
        "unit_div": 10_000_000.0,
        "is_indian": True,
        "rf": 0.071,
        "tax_rate": 0.25,
        "terminal_growth": 0.045,
        "terminal_roic": 0.45,
        "default_long_run_margin": 0.25,
        "default_beta": 0.82,
        "default_pe": 28.0,
    },
    {
        "keywords": ["reliance", "ril"],
        "name": "Reliance Industries Limited",
        "ticker": "RELIANCE",
        "sector": "Energy & Conglomerate",
        "industry": "Oil, Telecom & Retail",
        "exchange": "NSE / BSE",
        "currency": "₹",
        "currency_symbol": "₹",
        "unit_label": "₹ Crores",
        "unit_div": 10_000_000.0,
        "is_indian": True,
        "rf": 0.071,
        "tax_rate": 0.25,
        "terminal_growth": 0.050,
        "terminal_roic": 0.15,
        "default_long_run_margin": 0.16,
        "default_beta": 0.95,
        "default_pe": 26.5,
    },
    {
        "keywords": ["hdfc", "hdfcbank"],
        "name": "HDFC Bank Limited",
        "ticker": "HDFCBANK",
        "sector": "Financial Services",
        "industry": "Private Sector Bank",
        "exchange": "NSE / BSE",
        "currency": "₹",
        "currency_symbol": "₹",
        "unit_label": "₹ Crores",
        "unit_div": 10_000_000.0,
        "is_indian": True,
        "rf": 0.071,
        "tax_rate": 0.25,
        "terminal_growth": 0.055,
        "terminal_roic": 0.16,
        "default_long_run_margin": 0.32,
        "default_beta": 1.05,
        "default_pe": 18.5,
    },
    {
        "keywords": ["icici", "icicibank"],
        "name": "ICICI Bank Limited",
        "ticker": "ICICIBANK",
        "sector": "Financial Services",
        "industry": "Private Sector Bank",
        "exchange": "NSE / BSE",
        "currency": "₹",
        "currency_symbol": "₹",
        "unit_label": "₹ Crores",
        "unit_div": 10_000_000.0,
        "is_indian": True,
        "rf": 0.071,
        "tax_rate": 0.25,
        "terminal_growth": 0.055,
        "terminal_roic": 0.17,
        "default_long_run_margin": 0.30,
        "default_beta": 1.00,
        "default_pe": 17.5,
    },
    {
        "keywords": ["dr reddy", "drreddy", "dr. reddy"],
        "name": "Dr. Reddy's Laboratories Limited",
        "ticker": "DRREDDY",
        "sector": "Healthcare",
        "industry": "Pharmaceuticals & Generics",
        "exchange": "NSE / BSE",
        "currency": "₹",
        "currency_symbol": "₹",
        "unit_label": "₹ Crores",
        "unit_div": 10_000_000.0,
        "is_indian": True,
        "rf": 0.071,
        "tax_rate": 0.25,
        "terminal_growth": 0.050,
        "terminal_roic": 0.22,
        "default_long_run_margin": 0.22,
        "default_beta": 0.65,
        "default_pe": 21.0,
    },
    {
        "keywords": ["wipro"],
        "name": "Wipro Limited",
        "ticker": "WIPRO",
        "sector": "Information Technology",
        "industry": "IT Services & Consulting",
        "exchange": "NSE / BSE",
        "currency": "₹",
        "currency_symbol": "₹",
        "unit_label": "₹ Crores",
        "unit_div": 10_000_000.0,
        "is_indian": True,
        "rf": 0.071,
        "tax_rate": 0.25,
        "terminal_growth": 0.045,
        "terminal_roic": 0.18,
        "default_long_run_margin": 0.16,
        "default_beta": 0.90,
        "default_pe": 20.0,
    },
    {
        "keywords": ["tata motors", "tatamotors"],
        "name": "Tata Motors Limited",
        "ticker": "TATAMOTORS",
        "sector": "Automotive",
        "industry": "Commercial & Passenger Vehicles",
        "exchange": "NSE / BSE",
        "currency": "₹",
        "currency_symbol": "₹",
        "unit_label": "₹ Crores",
        "unit_div": 10_000_000.0,
        "is_indian": True,
        "rf": 0.071,
        "tax_rate": 0.25,
        "terminal_growth": 0.045,
        "terminal_roic": 0.18,
        "default_long_run_margin": 0.12,
        "default_beta": 1.25,
        "default_pe": 16.0,
    },
    {
        "keywords": ["itc"],
        "name": "ITC Limited",
        "ticker": "ITC",
        "sector": "Consumer Goods (FMCG)",
        "industry": "Cigarettes, FMCG & Hotels",
        "exchange": "NSE / BSE",
        "currency": "₹",
        "currency_symbol": "₹",
        "unit_label": "₹ Crores",
        "unit_div": 10_000_000.0,
        "is_indian": True,
        "rf": 0.071,
        "tax_rate": 0.25,
        "terminal_growth": 0.045,
        "terminal_roic": 0.30,
        "default_long_run_margin": 0.35,
        "default_beta": 0.70,
        "default_pe": 27.5,
    },
]

# Stop-words that must NEVER be treated as company name or ticker
STOP_TOKENS = {
    "AR", "ANNUAL", "REPORT", "REPORTS", "CONSOLIDATED", "STANDALONE",
    "FINANCIAL", "FINANCIALS", "STATEMENT", "STATEMENTS", "10K", "10Q",
    "10-K", "10-Q", "FORM", "QUARTERLY", "INTEGRATED", "THE", "OF", "FOR"
}


def _extract_bse_nse_filename_ticker(filename: str) -> Optional[str]:
    """
    Extracts ticker from standard exchange download filenames like:
    AR_29731_UNITDSPR_2025_2026_A_10956084_10072026221040.pdf -> UNITDSPR
    INFY_Annual_Report_2024.pdf -> INFY
    """
    fn = filename.upper()
    # Check BSE/NSE automated download pattern: AR_<scrip>_<SYMBOL>_...
    m = re.match(r"^AR_\d+_([A-Z0-9]+)_", fn)
    if m:
        sym = m.group(1).strip()
        if sym not in STOP_TOKENS:
            return sym

    # Check TICKER_Annual_Report... pattern
    m = re.match(r"^([A-Z0-9]+)[_\-\s]+(?:ANNUAL|10-K|10-Q|FINANCIAL|AR)", fn)
    if m:
        sym = m.group(1).strip()
        if sym not in STOP_TOKENS:
            return sym

    return None


def detect_company_from_document(pdf_path: str, filename: Optional[str] = None) -> Dict[str, Any]:
    """
    Universal corporate entity detector for filings from Indian (BSE/NSE) and Global (US SEC) exchanges.
    Parses document cover pages, exchange scrip codes, CIN, registrant headers, and filenames.
    """
    fn = (filename or os.path.basename(pdf_path))
    lower_fn = fn.lower()

    # 1. Check filename against known profiles
    for profile in KNOWN_PROFILES:
        for kw in profile["keywords"]:
            if kw in lower_fn:
                return dict(profile)

    # 2. Check if filename has an exchange-coded ticker (e.g. AR_29731_UNITDSPR_...)
    fn_ticker = _extract_bse_nse_filename_ticker(fn)
    if fn_ticker:
        for profile in KNOWN_PROFILES:
            if profile["ticker"].upper() == fn_ticker or fn_ticker.lower() in profile["keywords"]:
                return dict(profile)

    # 3. Read and normalize first 5 pages of PDF
    doc_text = ""
    try:
        doc = fitz.open(pdf_path)
        for i in range(min(5, len(doc))):
            raw_p = doc[i].get_text("text") or ""
            norm_p = unicodedata.normalize('NFKD', raw_p)
            doc_text += " " + norm_p
        doc.close()
    except Exception:
        pass

    lower_text = doc_text.lower()

    # 4. Check known profile keywords in normalized document text
    for profile in KNOWN_PROFILES:
        for kw in profile["keywords"]:
            if kw in lower_text:
                return dict(profile)

    # 5. Extract exchange scrip symbol or trading symbol directly from front matter
    scrip_m = re.search(r"(?:scrip\s+symbol|trading\s+symbol(?:s)?|nse\s+symbol)[:\s]+([A-Za-z0-9\-]+)", doc_text, re.IGNORECASE)
    scrip_sym = scrip_m.group(1).strip().upper() if scrip_m else None
    if scrip_sym and scrip_sym not in STOP_TOKENS:
        for profile in KNOWN_PROFILES:
            if profile["ticker"].upper() == scrip_sym or scrip_sym.lower() in profile["keywords"]:
                return dict(profile)

    # 6. Extract legal entity company name from front matter
    detected_name = None
    name_patterns = [
        # For United Spirits Limited / For XYZ Limited
        r"For\s+([A-Z][A-Za-z0-9\s,\.\(\)&'-]+?(?:Limited|Ltd|Corporation|Corp|Inc|Company|PLC|LLC))\b",
        # To the Members of XYZ Limited
        r"To\s+the\s+Members\s+of\s+([A-Z][A-Za-z0-9\s,\.\(\)&'-]+?(?:Limited|Ltd|Corporation|Corp|Inc|Company|PLC|LLC))\b",
        # Consolidated Financial Statements of XYZ Limited
        r"Consolidated\s+(?:Financial\s+Statements|Balance\s+Sheet|Statement\s+of\s+Profit\s+and\s+Loss)\s+of\s+([A-Z][A-Za-z0-9\s,\.\(\)&'-]+?(?:Limited|Ltd|Corporation|Corp|Inc|Company|PLC|LLC))\b",
        # SEC 10-K: EXACT NAME OF REGISTRANT AS SPECIFIED IN ITS CHARTER: XYZ CORP
        r"EXACT\s+NAME\s+OF\s+REGISTRANT[^\n]*\n+([A-Z0-9\s,\.\(\)&'-]{3,60})\b",
    ]
    for pat in name_patterns:
        m = re.search(pat, doc_text)
        if m:
            candidate = m.group(1).strip()
            # Clean up newlines or excessive spaces
            candidate = re.sub(r"\s+", " ", candidate).strip()
            if len(candidate) > 3 and not any(candidate.upper().startswith(st) for st in STOP_TOKENS):
                detected_name = candidate
                break

    # Determine geography / currency / exchange
    is_usd = (
        "$" in doc_text
        or "form 10-k" in lower_text
        or "form 10-q" in lower_text
        or "securities and exchange commission" in lower_text
        or "delaware" in lower_text
        or "united states" in lower_text
    )
    is_inr = (
        "₹" in doc_text
        or "rupees" in lower_text
        or "crores" in lower_text
        or "lakhs" in lower_text
        or "bse" in lower_text
        or "nse" in lower_text
        or "mca" in lower_text
        or "sebi" in lower_text
        or "ind as" in lower_text
        or bool(re.search(r"\b[LU][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}\b", doc_text))
    )
    is_indian = is_inr or (not is_usd)

    # Resolve Company Name
    if not detected_name:
        # If filename ticker was found, use it
        if fn_ticker:
            detected_name = f"{fn_ticker.title()} Limited" if is_indian else f"{fn_ticker.upper()} Inc."
        else:
            clean_title = re.sub(r"[_.-]", " ", os.path.basename(pdf_path).replace(".pdf", "")).strip().title()
            words = [w for w in clean_title.split() if w.upper() not in STOP_TOKENS]
            detected_name = " ".join(words) if words else clean_title

    # Resolve Ticker
    ticker = None
    if scrip_sym and scrip_sym not in STOP_TOKENS:
        ticker = scrip_sym
    elif fn_ticker:
        ticker = fn_ticker
    else:
        # Build ticker from detected company name words
        words = [w for w in re.sub(r"[^\w\s]", "", detected_name).split() if w.upper() not in STOP_TOKENS and w.upper() not in {"LIMITED", "LTD", "INC", "CORP", "CORPORATION", "COMPANY", "PLC", "LLC"}]
        if words:
            ticker = words[0].upper() if len(words) == 1 else "".join(w[0] for w in words[:4]).upper()
        else:
            ticker = "CORP"

    # Clean ticker if accidental stop token
    if ticker in STOP_TOKENS or len(ticker) < 2:
        ticker = "CO-FILING"

    return {
        "keywords": [],
        "name": detected_name,
        "ticker": ticker,
        "sector": "Diversified Business" if not is_usd else "Corporate Technology",
        "industry": "Commercial & Industrial Operations",
        "exchange": "NSE / BSE" if is_indian else "US Exchange (NASDAQ/NYSE)",
        "currency": "₹" if is_indian else "$",
        "currency_symbol": "₹" if is_indian else "$",
        "unit_label": "₹ Crores" if is_indian else "$ Millions",
        "unit_div": 10_000_000.0 if is_indian else 1_000_000.0,
        "is_indian": is_indian,
        "rf": 0.071 if is_indian else 0.040,
        "tax_rate": 0.25 if is_indian else 0.18,
        "terminal_growth": 0.045 if is_indian else 0.025,
        "terminal_roic": 0.20,
        "default_long_run_margin": 0.20,
        "default_beta": 1.0,
        "default_pe": 24.0,
    }
