# DATA STRATEGY & BENCHMARKING GUIDE (NSE / BSE FOCUS)

## 1. Overview
FinSight AI targets real corporate filings from Indian listed companies on the **National Stock Exchange (India) [NSE]** and the **Bombay Stock Exchange [BSE]**, operating under Indian Accounting Standards (**Ind AS**) aligned with IFRS.

The platform processes:
1. **Primary PDF Filings**: Annual Reports filed under SEBI Listing Obligations and Disclosure Requirements (LODR) Regulations, 2015.
2. **Standard Financial Statements**:
   - Consolidated Balance Sheet
   - Consolidated Statement of Profit and Loss
   - Consolidated Statement of Cash Flows
   - Notes to Financial Statements & Segment Reporting
3. **Ground Truth Validation**:
   - For companies with cross-listed American Depositary Receipts (ADRs) (e.g., Infosys `INFY`, Wipro `WIT`, HDFC Bank `HDFCBANK`, Dr. Reddy's `DRREDDY`), authoritative SEC XBRL `companyfacts` JSON taxonomies (`ifrs-full`) serve as mathematical ground truth.
   - For domestic-only entities, SEBI/BSE audited filing disclosures serve as the benchmark.

---

## 2. Company Universe & Registry

| Symbol (NSE/BSE) | Company Name | Sector | Filing Format | Ground Truth Source |
|---|---|---|---|---|
| `INFY` / `500209` | Infosys Limited | Information Technology | BSE Integrated Annual Report (PDF) | SEC IFRS XBRL (`CIK0001067491`) |
| `TCS` / `532540` | Tata Consultancy Services | Information Technology | BSE Integrated Annual Report (PDF) | BSE Audited Results |
| `HDFCBANK` / `500180` | HDFC Bank Limited | Financial Services (Banking) | BSE Annual Report (PDF) | SEC IFRS XBRL (`CIK0001144967`) |
| `WIPRO` / `507685` | Wipro Limited | Information Technology | BSE Integrated Annual Report (PDF) | SEC IFRS XBRL (`CIK0001123799`) |
| `DRREDDY` / `500124` | Dr. Reddy's Laboratories | Healthcare & Pharma | BSE Annual Report (PDF) | SEC IFRS XBRL (`CIK0001135951`) |
| `RELIANCE` / `500325` | Reliance Industries | Energy & Conglomerate | BSE Integrated Annual Report (PDF) | BSE Audited Results |
| `ITC` / `500875` | ITC Limited | Consumer Staples (FMCG) | BSE Annual Report (PDF) | BSE Audited Results |
| `TATAMOTORS` / `500570` | Tata Motors Limited | Consumer Discretionary | BSE Annual Report (PDF) | BSE Audited Results |

---

## 3. Rate Limiting and Responsible Access Policy
- **BSE Static CDNs / Attachments**: Custom desktop browser `User-Agent` and `Referer: https://www.bseindia.com/` headers with a minimum 1.0s throttle between requests.
- **SEC EDGAR API (Ground Truth)**: Custom `User-Agent: FinSightAI research@finsight-ai.edu`, strictly limited to <10 requests/sec with exponential backoff on HTTP 429.
- **Illustrative Universe**: 30+ pre-calibrated companies in `data/sample_universe/companies.py` are explicitly marked as **ILLUSTRATIVE** until live PDF ingestion occurs.

---

## 4. Phase A Baseline Benchmark Findings
- **Document Tested**: Infosys FY24 Integrated Annual Report (`INFOSYS_BSE_Annual_Report_2023_24.pdf`, 384 pages).
- **Initial Regex Extractor Baseline Failure Rate**: **100% failure rate (0 metrics extracted)** on unformatted text lines.
- **Root Causes Identified**:
  1. **Borderless multi-column tables**: Financial tables in Indian annual reports do not use bordered gridlines, causing classic `pdfplumber.extract_tables()` to find 0 tables.
  2. **Indian Numbering formatting**: Comma placements such as `1,78,650` (lakhs/crores) violated Western thousands regex `\d{1,3}(?:,\d{3})+`.
  3. **Multi-line column fragmentation**: Plain string splitting separated metric titles, note numbers (e.g. `2.18`), and value columns across separate lines.
- **Resolution Plan for Phase B & C**:
  - Implement coordinate/block-level geometric line clustering (PyMuPDF `get_text("blocks")` and visual table layout).
  - Add native support for Indian numbering and Crores/Lakhs currency symbols (`₹`, `` ` ``).
