# PROJECT_CONTEXT.md
**FinSight AI — Financial Document Intelligence & Investment Recommendation System**

> READ THIS FILE FIRST IN EVERY NEW SESSION.
> This is the single source of truth for the project. Whenever you (Claude) resume work, upload this file back (or the whole project zip) and say "continue from PROJECT_CONTEXT.md". Update the **Progress Log** and **Current State** sections every time you finish a module, and re-export a new version of the project zip.

---

## 1. What this project is

An AI platform that turns unstructured corporate financial documents (annual reports, quarterly reports, ESG reports, investor presentations) into structured financial data, then runs financial analytics + a hybrid recommendation engine to produce **explainable, personalized investment recommendations**. Not a chatbot, not a plain PDF summarizer.

Full original spec is preserved in `docs/ORIGINAL_SPEC.md` — treat that as the requirements doc. This file (`PROJECT_CONTEXT.md`) is the living build log / architecture decision record.

---

## 2. Critical review of the original spec (done in session 1)

**Verdict:** the spec is a strong, complete final-system design, but far too large to build in one shot. Key simplifications applied for the MVP:

| Original ask | MVP decision | Why |
|---|---|---|
| PostgreSQL | Start with **SQLite** via SQLAlchemy (same ORM code, swap connection string later) | Zero setup friction, identical code path to Postgres later |
| Tesseract/PaddleOCR full OCR pipeline | Stub module now, wire in Phase 1b only if a scanned PDF is actually encountered | Most annual reports are digitally generated; OCR is a real but secondary cost center |
| Camelot + pdfplumber table extraction | Start with **pdfplumber only** | Camelot needs Ghostscript system dependency, adds install friction; pdfplumber covers most bordered/unbordered tables |
| Full 15-dim feature vector, K-Means, cosine similarity, hybrid engine | Build in Phase 4, **after** extraction + DB are proven on 2–3 real PDFs | Per user's own instruction #37/#38: don't jump to the complex system first |
| React production frontend | Streamlit only for now | Matches MVP frontend spec, fastest iteration |
| FastAPI backend | Keep — it's not extra complexity, it's the right shape from day 1 | Lets Streamlit AND future React call the same API |

**Unnecessary complexity flagged (deferred, not deleted from vision):** DCF intrinsic valuation, Beta/volatility market-risk module, ESG scraping, full explainability LLM layer. These need external market data (price history) which is a separate integration — deferred to Phase 4/5.

---

## 3. Final MVP scope (Phase 1, THIS is what's built first)

1. Upload a PDF annual report via FastAPI endpoint (and Streamlit UI).
2. Extract raw text per page (PyMuPDF), flag pages with little/no extractable text as "likely scanned" (OCR stub raises NotImplemented placeholder for those, doesn't crash).
3. Extract tables per page (pdfplumber).
4. Regex/keyword-based financial metric extractor pulls: Revenue, Net Income, Total Assets, Total Liabilities, Total Debt, Shareholders' Equity, Operating Cash Flow, CapEx.
5. Each extracted metric stored with: value, year, source page, document name, extraction method, confidence — per spec section 10.
6. Validation rules (Assets ≈ Liabilities + Equity, FCF = OCF - CapEx) flag inconsistent values.
7. Store into SQLite via SQLAlchemy models mirroring the spec's table design (companies, financial_metrics, esg_metrics stub, user_preferences).
8. Compute Phase-3-lite ratios: Revenue Growth, ROE, Debt-to-Equity, Free Cash Flow.
9. Minimal recommendation: hard filters (risk tolerance → max D/E, ESG placeholder) + simple weighted score across the 4 ratios above, output ranked list with a plain-language explanation built from the actual numbers (no LLM invention).
10. Streamlit dashboard: upload → view extracted metrics with page citations → view ratios → set preferences → get ranked recommendation with explanation.

This is intentionally the full pipeline end-to-end, but shallow at every step. Depth (OCR, more metrics, cosine similarity, K-Means, ESG, DCF, valuation, market risk, React) comes in Phases 2–6, in the order given in spec section 38.

---

## 4. Architecture (MVP)

```
Streamlit UI  ─calls──▶  FastAPI (api/main.py)
                              │
                 ┌────────────┼─────────────┐
                 ▼            ▼              ▼
      document_processing  extraction   database (SQLAlchemy/SQLite)
      (pdf_loader,          (financial_       │
       text_extractor,       extractor,       ▼
       table_extractor,      validation)  analytics (ratios, scoring)
       ocr stub)                              │
                                               ▼
                                    recommendation (filters, scoring, explain)
```

---

## 5. Folder structure (as built)

```
financial-document-intelligence/
├── PROJECT_CONTEXT.md          ← this file, always re-read first
├── docs/
│   └── ORIGINAL_SPEC.md        ← verbatim original requirements
├── data/
│   ├── raw_documents/          ← uploaded PDFs land here
│   ├── extracted_text/         ← per-doc JSON of extracted text/tables
│   └── processed_data/         ← finsight.db (SQLite) lives here
├── document_processing/
│   ├── pdf_loader.py
│   ├── text_extractor.py
│   ├── table_extractor.py
│   └── ocr.py                  ← stub, Phase 1b
├── extraction/
│   ├── financial_extractor.py
│   └── validation.py
├── analytics/
│   ├── financial_metrics.py    ← ratio calculations
│   └── scoring.py              ← weighted investment score
├── recommendation/
│   ├── filters.py               ← hard filters
│   └── explain.py               ← builds plain-language reasons from real numbers
├── database/
│   ├── models.py                ← SQLAlchemy models
│   └── database.py              ← engine/session setup
├── api/
│   └── main.py                  ← FastAPI app, all endpoints
├── frontend/
│   └── app.py                   ← Streamlit dashboard
├── tests/
│   └── test_phase1.py
├── requirements.txt
└── README.md                    ← setup + run instructions
```

---

## 6. Tech stack decisions (locked for MVP)

- Python 3.11+
- FastAPI + Uvicorn
- PyMuPDF (`fitz`) — native text extraction
- pdfplumber — table extraction
- SQLAlchemy + SQLite (Postgres-ready, swap `DATABASE_URL` later)
- Pandas / NumPy — analytics
- scikit-learn — reserved for Phase 4 (StandardScaler, KMeans, cosine similarity)
- Streamlit — MVP frontend

---

## 7. Progress Log

> Append a new dated entry every session. Never delete old entries.

- **Session 1 (2026-08-29):** Reviewed spec. Locked MVP scope (section 3). Created folder structure, PROJECT_CONTEXT.md, and Phase 1 code: pdf_loader, text_extractor, table_extractor, ocr stub, financial_extractor, validation, database models, analytics ratios, minimal recommendation + explanation, FastAPI endpoints, Streamlit UI, requirements.txt, README. Status: Phase 1 MVP code written.
- **Session 2 (2026-08-29):** Implemented the full end-to-end multi-module system (Phases 1–6):
  1. Synthetic Annual Report Generator (`data/generate_sample_reports.py`) producing realistic multi-page 10-K PDFs with multi-year tables, unit headers, and MD&A for 5 diverse companies (AAPL, NVDA, PFE, TSLA, NEE).
  2. Section Identification module (`document_processing/section_identifier.py`) recognizing Income Statement, Balance Sheet, Cash Flow, MD&A, Risk Factors, Notes, and ESG.
  3. Unit-scaled extraction & multi-year parsing in `extraction/financial_extractor.py`.
  4. Complete financial ratios (CAGR, Gross/Operating/Net Margins, ROIC, Current Ratio, DCF Intrinsic Value & Upside) in `analytics/financial_metrics.py`.
  5. 15-dimensional standardized Financial Feature Vector with `MinMaxScaler`/`StandardScaler` in `analytics/feature_vector.py`.
  6. Category-level scoring across 6 pillars (Growth, Profitability, Health, Valuation, Risk, ESG) + weighted composite score in `analytics/scoring.py`.
  7. Cosine Similarity matching engine in `recommendation/similarity.py`.
  8. K-Means clustering and archetype classification engine in `recommendation/clustering.py`.
  9. Constraint-based hard filter engine in `recommendation/filters.py`.
  10. Full Hybrid Recommendation Engine pipeline in `recommendation/hybrid_engine.py`.
  11. Grounded Explainable AI rationale generator in `recommendation/explain.py`.
  12. Upgraded FastAPI backend with multi-company endpoints in `api/main.py`.
  13. Upgraded interactive 4-tab Streamlit dashboard in `frontend/app.py`.
  14. Comprehensive test suite (`tests/test_full_pipeline.py` & `tests/test_phase1.py`) with 28 passing unit and integration tests.
- **Session 3 (2026-09-22):** Prepared the project for publication: synchronized the README with the completed Phase 1–6 capability, aligned the Streamlit API default with the documented port (8000), and expanded Git ignore coverage for local secrets and virtual environments. Automated runtime verification is pending a usable local Python environment with the project dependencies installed.
- **Session 4 (2026-10-10) — Phase A Hardening & Real Data (NSE / BSE Focus):**
  1. Fixed missing function exports (`rank_companies`, `recommend_for_portfolio`) in `recommendation/similarity.py`, bringing all baseline tests to green.
  2. Fixed clustering risk: removed hardcoded cluster index labeling fallback, implemented centroid-derived archetypes (`label_cluster_by_centroid`) and auto-$k$ optimization via Silhouette Score (`determine_optimal_k`).
  3. Reoriented the core universe from global exchanges to Indian stock exchanges (**National Stock Exchange [NSE] & Bombay Stock Exchange [BSE]**):
     - Created `data_adapters/indian_market_downloader.py` supporting BSE corporate report downloads and SEC cross-listed Indian ADR XBRL ground truth facts.
     - Updated `data/sample_universe/companies.py` to 30+ major Indian blue chips across 6 diverse sectors (IT, Banking & Financial Services, Energy & Conglomerate, Healthcare & Pharma, Automotive & Industrials, Consumer FMCG).
     - Downloaded real multi-page BSE Integrated Annual Report for **Infosys Limited (`INFY`)** (384 pages) and SEC cross-filings + XBRL ground truth facts for INFY, Wipro (`WIPRO`), HDFC Bank (`HDFCBANK`), and Dr. Reddy's (`DRREDDY`).
  4. Executed Phase A extraction baseline benchmark against the real Infosys PDF filing:
     - Documented a **100% baseline failure rate (0 metrics extracted)** on the initial regex extractor.
     - Identified 3 key architectural gaps: borderless table detection failure, Indian comma formatting (`1,78,650`), and line-level text fragmentation between metric labels, note citations (`2.18`), and values.
     - Documented findings and data strategy in `docs/DATA.md`.
  5. All 39 test cases passing cleanly on Python 3.12 (`tests/test_full_pipeline.py`, `tests/test_phase1.py`, `tests/test_similarity.py`).
- **Session 5 (2026-10-10) — Phase B Computer Vision Pipeline:**
  1. Built high-resolution 300 DPI page renderer (`vision/page_renderer.py`) using PyMuPDF and PIL, supporting both full-fidelity page renders and thumbnail grids.
  2. Built Ind AS / IFRS document page-type classifier (`vision/page_classifier.py`) identifying Balance Sheet, Profit and Loss Statement, Statement of Cash Flows, Notes, and Auditor's Reports.
  3. Built geometric / borderless table layout extraction engine (`vision/table_layout.py`) that clusters words into horizontal statement rows using vertical coordinate tolerance, separates line-item labels from note citations, and extracts multi-year column values with exact bounding boxes.
  4. Built OCR engine (`vision/ocr_engine.py`) detecting scanned pages (<20 native characters) with selective OCR fallback and per-token confidence tracking.
  5. Built visual bounding box overlay generator (`vision/visual_overlay.py`) producing color-coded annotations (Income, Balance Sheet, Cash Flow, Notes) on rendered document pages.
  6. Verified against real Infosys Ind AS Annual Report statement pages with 5 new unit/integration tests in `tests/test_vision_pipeline.py`.
  7. All 44 test cases passing cleanly on Python 3.12.

- **Session 6 (2026-10-10) — Phase C Multi-Period Statements, Validations & Full Ratio Library:**
  1. Built multi-period statement extraction engine (`extraction/statement_extractor.py`) incorporating coordinate table layout geometry to extract multi-year columns (latest year, prior year, historicals) with exact bounding box citations (doc, page, bbox, confidence). Successfully extracted 34 unique statement metrics on the real Infosys Ind AS filing (including Revenue of ₹1,78,650 Cr, Net Income of ₹29,474 Cr, Total Assets of ₹1,55,967 Cr).
  2. Built accounting identity validation & empirical data quality scoring engine (`extraction/accounting_validator.py`):
     - Validates Balance Sheet integrity (Assets == Liabilities + Equity), P&L flow, and Free Cash Flow tie-outs.
     - Computes an empirical Data Quality Score (0 to 100) and outputs human-readable audit warnings.
  3. Built comprehensive quantitative finance ratio library (`analytics/ratio_library.py`):
     - Profitability: Gross/Operating/Net Margins, ROE, ROA, ROIC, ROCE.
     - Liquidity & Leverage: Current Ratio, Quick Ratio, Cash Ratio, Debt-to-Equity, Debt-to-Assets, Interest Coverage, Net Debt/EBITDA.
     - DuPont Analysis: 3-step DuPont and 5-step DuPont (Tax Burden × Interest Burden × Operating Margin × Asset Turnover × Leverage).
     - Financial Health & Bankruptcy Risk: 9-point Piotroski F-Score and Altman Z-Score (Emerging Market / Non-manufacturing safe/grey/distress zones).
  4. Built Trailing Twelve Months (TTM) calculation engine (`analytics/ttm_engine.py`):
     - `TTM = Latest Annual + Current YTD(Interim) - Prior YTD(Interim)`.
  5. Verified with 5 new unit/integration tests in `tests/test_phase_c_ratios.py`.
  6. All 49 test cases passing cleanly on Python 3.12.
- **Session 7 (2026-10-10) — Phase D Full DCF Valuation Engine:**
  1. Built WACC calculator via CAPM (`valuation/wacc_calculator.py`):
     - Cost of Equity ($K_e = R_f + \beta \times \text{ERP}$) using Indian sovereign 10Y yield and emerging market ERP.
     - After-tax Cost of Debt ($K_d = (I / D) \times (1 - t)$).
     - Market-value capital structure weighting ($W_e, W_d$).
  2. Built FCFF driver & projection engine (`valuation/fcff_engine.py`):
     - 5-year forecast horizon with mid-year discounting toggle ($t - 0.5$).
     - Reinvestment model: $\text{FCFF} = \text{EBIT} \times (1 - t) + \text{D&A} - \text{CapEx} - \Delta \text{NWC}$.
  3. Built complete DCF valuation engine (`valuation/dcf_engine.py`):
     - Enterprise Value: $\text{EV} = \sum \text{PV}(\text{FCFF}) + \text{PV}(\text{TV})$.
     - Dual Terminal Value methods: Gordon Growth vs. Exit Multiple with implied cross-checks (implied multiple from Gordon, implied $g$ from multiple) and TV share of EV warnings (>75%).
     - Cited Equity Bridge: $\text{EV} - \text{Debt} - \text{Leases} - \text{Preferred} - \text{NCI} + \text{Cash} = \text{Equity Value} \div \text{Shares} \to \text{Value per share}$ and upside.
     - 2D Sensitivity table ($\text{WACC} \times \text{Terminal Growth}$).
     - Reverse DCF solving for market-implied growth rate from current stock price via binary search.
  4. Verified with 5 new unit/integration tests in `tests/test_dcf_valuation.py` including hand-calculated worked example and guardrails ($WACC \le g \to \text{ValueError}$).
  5. All 54 test cases passing cleanly on Python 3.12.

- **Session 8 (2026-10-10) — Phase E Recommendation Systems & Collaborative Filtering:**
  1. Built institutional holdings Collaborative Filtering engine (`recommendation/collaborative_filter.py`):
     - Item-to-Item cosine similarity over institutional portfolio holdings (FII/DII / 13F-style).
     - Matrix Factorization via `TruncatedSVD`.
     - Deterministic cold-start fallback to content-based similarity for unrated/newly uploaded companies.
  2. Built recommendation evaluation suite (`recommendation/eval_metrics.py`):
     - Precision@K, Recall@K, NDCG@K, Catalog Coverage, and Intra-List Diversity metrics.
  3. Blended collaborative filtering signals into `recommendation/hybrid_engine.py`.
  4. Verified with 4 unit/integration tests in `tests/test_recommender_phase_e.py`.
  5. 58/58 test cases passing cleanly on Python 3.12.

- **Session 9 (2026-10-10) — Phase F Equity Research Reporting & Streamlit/FastAPI UI Integration:**
  1. Built institutional Equity Research Report PDF generator (`reporting/report_generator.py`) using ReportLab:
     - Header & Title Block (Company name, Ticker, Exchange, Sector, Current Price, Date).
     - Rule-derived recommendation rating (`STRONG BUY`, `BUY`, `HOLD`, `UNDERPERFORM`, `SELL`) with explicit mathematical thresholds and actions.
     - Document extraction & audit citations table with source page numbers, bounding box coordinates, and extraction methods.
     - Comprehensive financial ratio dashboard (Operating Margin, ROE, DuPont 3-Step, Solvency, Piotroski F-Score, Altman Z-Score).
     - DCF valuation summary with WACC parameters, 5-year FCFF, cited Equity Bridge, 2D WACC vs. Growth sensitivity matrix, and TV share warnings.
     - Peer comp recommendations with Content Similarity, CF Score, Cluster Archetype, and Hybrid Match.
     - Full regulatory disclaimer (educational research compliance).
  2. Integrated end-to-end institutional pipeline into FastAPI (`api/main.py`):
     - `/pipeline/full/{document_id}` executes Vision ➔ Audits ➔ Ratios ➔ DCF ➔ Peers ➔ PDF report compilation.
     - `/report/{document_id}` serves the compiled PDF report.
  3. Added Tab 5 to Streamlit dashboard (`frontend/app.py`):
     - Interactive parameters, end-to-end pipeline execution button, DCF summary metrics, accounting verification results, and one-click PDF report download.
  4. Verified with 2 new unit/integration tests in `tests/test_report_generator.py`.
  5. 60/60 test cases passing cleanly on Python 3.12.

- **Session 10 (2026-10-10) — Phase G Documentation & Viva Readiness:**
  1. Authored complete system architecture document in `docs/ARCHITECTURE.md` with Mermaid diagram, module mapping, and empirical benchmark tables.
  2. Authored defense presentation cheat-sheet in `docs/VIVA_CHEAT_SHEET.md` with Q&A covering Computer Vision, Borderless Table Layouts, DCF Guardrails, and Collaborative Filtering Recommender metrics.

- **Session 11 (2026-10-18) — Aesthetic DCF Studio & Full System Completion:**
  1. Integrated the architecture, mechanics, and design system of `zi-cong-tan/DCF-Calculator-Aesthetic` into the platform:
     - Built `valuation/aesthetic_dcf.py` implementing `AestheticDCFFacts`, `AestheticDCFAssumptions`, `AestheticDCFEngine`, 10-year mid-year discounting projections, ROIC-driven terminal reinvestment, binary-search reverse DCF for implied margin, and 5x5 sensitivity matrix with nearest-market-price highlighting.
     - Added `POST /dcf/aesthetic/{document_id}` endpoint in `api/main.py`.
     - Integrated the Aesthetic DCF Interactive Studio into Tab 5 of `frontend/app.py` with custom CSS, Hero stat banner, locked accounting facts vs editable judgment knobs, waterfall equity bridge, and 5x5 sensitivity matrix.
     - Created `tests/test_aesthetic_dcf.py` with unit tests verifying valuation math, implied margin bisection, and sensitivity grids.
  2. Executed complete 10-point system audit across all modules and pipelines (Health, Seed, Ingestion, Extraction, Traceability, Accounting Audits, Ratios, Peer Clustering, Hybrid Recommendations, Aesthetic DCF, and PDF Equity Research Report Generation).
  3. All 63 unit and integration tests passing cleanly on Python 3.12.

- **Session 12 (2026-10-18) — Modern Web Application Frontend, Any NSE/BSE Stock Screener, and CV Pipeline Hardening:**
  1. Built a complete modern Single-Page Application (SPA) web frontend at `static/index.html`, `static/app.css`, and `static/app.js` served directly by FastAPI at `http://127.0.0.1:8000/` and `/dashboard`. Features:
     - Document Intelligence & Upload panel (Annual Reports, Standalone, Consolidated, 10-K, 10-Q).
     - Computer Vision Inspector with 300 DPI page rendering and bounding box overlay canvas.
     - Screener.in / StockAnalysis multi-year statement tables (P&L, Balance Sheet, Cash Flow, Quarterly 10-Q).
     - Financial Ratio Diagnostic cards (Current, Quick, Assets/Liabilities, Piotroski F-score, Altman Z-score, 5-Step DuPont).
     - Aesthetic DCF Valuation Studio with interactive judgment knobs, cash flow projections, and 5x5 sensitivity matrix.
     - One-click institutional equity research PDF report download.
  2. Implemented universal stock screener & filing explorer (`data_adapters/company_filings_adapter.py`) enabling users to search and analyze **ANY** company on NSE, BSE, or global exchanges, with direct official filing links to BSE Announcements, NSE Filings, and SEC EDGAR 10-K/10-Q.
  3. Added Standalone vs. Consolidated scope detection and 10-K vs. 10-Q filing type tagging in `extraction/statement_extractor.py`.
  4. Added `THIRD_PARTY_NOTICES.md` with full MIT License attribution for `zi-cong-tan/DCF-Calculator-Aesthetic`.
  5. Added `data/dcf_reference_examples.json` with reference models for MU, AAPL, AMZN, and TSLA, plus `valuation/dcf.py` compatibility wrapper and `tests/fixtures/dcf_reference.json`.

---

## 8. Current State (update this block every session — this is what "resume" reads)

- **Last completed phase:** Phase G + Aesthetic DCF Studio + Modern Web Application Frontend & Any NSE/BSE Stock Screener.
- **Verified Status:**
  - **Modern Web Application**: Live at `http://127.0.0.1:8000/` and `http://127.0.0.1:8000/dashboard`.
  - **Streamlit Companion UI**: Live at `http://localhost:8501`.
  - **Computer Vision Pipeline**: 300 DPI high-res page rasterization, 2D coordinate table layout clustering ($\Delta y \le 3.5\text{ pt}$), Ind AS/IFRS statement classification, Standalone vs. Consolidated detection, visual bounding box heatmap overlays, and sub-pixel traceable coordinate citations.
  - **Screener.in & StockAnalysis Integration**: Multi-year Annual (10-K) and Quarterly (10-Q) statements, balance sheets, cash flows, and direct official filing URLs for ANY company on NSE/BSE.
  - **Aesthetic DCF Valuation Studio**: 10-year mid-year discounting, reverse DCF implied margin bisection, locked accounting facts vs editable judgment knobs, and 5x5 WACC vs Margin sensitivity matrix.
  - **Accounting Validations & Forensic Scoring**: Assets = Liabilities + Equity tie-outs, FCF = OCF - CapEx, Piotroski F-Score (0-9), Altman Z-Score, and 5-step DuPont ROE decomposition.
  - **Attributions**: MIT License attribution in `THIRD_PARTY_NOTICES.md`.
- **Next steps:** Ready for final project submission, viva defense, and live demonstration!





