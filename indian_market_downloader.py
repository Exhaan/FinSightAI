"""
Data Adapter for Indian Stock Exchanges (NSE / BSE) and Corporate Filings.

Provides:
- Real annual report discovery & download for BSE / NSE listed companies.
- SEC cross-listed Indian ADR 20-F filings & XBRL ground truth facts.
- Rate-limiting and error handling with custom User-Agent headers.
"""
import os
import json
import time
import urllib.request
from typing import Optional, Dict, Any, List

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
SEC_USER_AGENT = "FinSightAI research@finsight-ai.edu"

# Mapping of prominent Indian companies across diverse sectors
INDIAN_COMPANIES_REGISTRY = {
    "INFY": {
        "name": "Infosys Limited",
        "bse_scrip": "500209",
        "nse_symbol": "INFY",
        "sector": "Information Technology",
        "sec_cik": "0001067491",
        "bse_pdf_url": "https://www.bseindia.com/xml-data/corpfiling/AttachHis/089c483b-7ab1-476a-8314-45bca94336f2.pdf",
    },
    "TCS": {
        "name": "Tata Consultancy Services Limited",
        "bse_scrip": "532540",
        "nse_symbol": "TCS",
        "sector": "Information Technology",
        "sec_cik": None,
    },
    "RELIANCE": {
        "name": "Reliance Industries Limited",
        "bse_scrip": "500325",
        "nse_symbol": "RELIANCE",
        "sector": "Energy & Conglomerate",
        "sec_cik": None,
    },
    "HDFCBANK": {
        "name": "HDFC Bank Limited",
        "bse_scrip": "500180",
        "nse_symbol": "HDFCBANK",
        "sector": "Financial Services (Banking)",
        "sec_cik": "0001144967",
    },
    "ICICIBANK": {
        "name": "ICICI Bank Limited",
        "bse_scrip": "532174",
        "nse_symbol": "ICICIBANK",
        "sector": "Financial Services (Banking)",
        "sec_cik": "0001103838",
    },
    "WIPRO": {
        "name": "Wipro Limited",
        "bse_scrip": "507685",
        "nse_symbol": "WIPRO",
        "sector": "Information Technology",
        "sec_cik": "0001123799",
    },
    "DRREDDY": {
        "name": "Dr. Reddy's Laboratories Limited",
        "bse_scrip": "500124",
        "nse_symbol": "DRREDDY",
        "sector": "Healthcare & Pharmaceuticals",
        "sec_cik": "0001135951",
    },
    "TATAMOTORS": {
        "name": "Tata Motors Limited",
        "bse_scrip": "500570",
        "nse_symbol": "TATAMOTORS",
        "sector": "Automotive",
        "sec_cik": None,
    },
    "ITC": {
        "name": "ITC Limited",
        "bse_scrip": "500875",
        "nse_symbol": "ITC",
        "sector": "Consumer Goods (FMCG)",
        "sec_cik": None,
    },
}


class IndianFilingDownloader:
    """
    Downloads real financial filings for Indian companies listed on NSE and BSE.
    Supports BSE corporate announcements, direct corporate links, and SEC dual-filings.
    """

    def __init__(self, output_dir: str = "data/raw_documents", rate_limit_delay: float = 1.0):
        self.output_dir = output_dir
        self.rate_limit_delay = rate_limit_delay
        os.makedirs(self.output_dir, exist_ok=True)

    def download_filing_pdf(self, url: str, output_filename: str) -> str:
        """
        Downloads a PDF filing with appropriate headers for BSE / Indian CDNs.
        """
        out_path = os.path.join(self.output_dir, output_filename)
        headers = {
            "User-Agent": DEFAULT_USER_AGENT,
            "Referer": "https://www.bseindia.com/",
            "Accept": "application/pdf,*/*",
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=45) as resp:
            content = resp.read()
            with open(out_path, "wb") as f:
                f.write(content)
        time.sleep(self.rate_limit_delay)
        return out_path

    def download_sec_facts(self, cik: str, company_name: str, ground_truth_dir: str = "data/ground_truth") -> str:
        """
        Downloads authoritative XBRL companyfacts for Indian companies with cross-listed ADRs.
        """
        os.makedirs(ground_truth_dir, exist_ok=True)
        out_path = os.path.join(ground_truth_dir, f"{company_name}_facts.json")
        cik_clean = cik.zfill(10)
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_clean}.json"
        headers = {"User-Agent": SEC_USER_AGENT}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read()
            with open(out_path, "wb") as f:
                f.write(content)
        time.sleep(self.rate_limit_delay)
        return out_path
