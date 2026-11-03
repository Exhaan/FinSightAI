# FinSight AI — Financial Document Intelligence & Investment Recommendation System

**Status: complete local MVP (Phases 1–6)** — document extraction, financial
analytics, peer comparison, clustering, and grounded investment recommendations.
See **`PROJECT_CONTEXT.md`** for the full architecture, decisions, progress log, and next steps —
read that file first when resuming work in a new session.

Full original requirements are preserved in `docs/ORIGINAL_SPEC.md`.

---

## What works right now

- Upload a PDF annual report
- Native text extraction per page (PyMuPDF), with scanned-page detection
- Table extraction (pdfplumber)
- Regex/keyword-based extraction of core metrics (Revenue, Net Income, Total
  Assets, Total Liabilities, Total Debt, Shareholders' Equity, Operating Cash
  Flow, CapEx, Gross Profit, Cost of Revenue) — each with page number,
  extraction method, and confidence score (full traceability)
- Validation rules (Assets ≈ Liabilities+Equity, FCF = OCF−CapEx, etc.) that
  flag inconsistencies instead of silently trusting extracted numbers
- SQLite database storing documents, extracted metrics, companies
- Ratio calculations: Revenue Growth, ROE, Debt-to-Equity, Free Cash Flow
- 15-dimensional financial feature engineering and normalization
- Category-level scoring across growth, profitability, financial health, valuation,
  risk, and ESG pillars
- Multi-company comparison, cosine-similarity matching, and K-Means investor archetypes
- A hybrid, explainable investment recommendation engine
- Hard filters based on user preferences (max D/E, min ROE, min growth)
- A plain-language explanation of strengths/risks built ONLY from computed
  numbers (no invented figures)
- FastAPI backend + Streamlit dashboard, end to end

## Current limitations

- OCR for scanned pages (stubbed, raises a clear "not implemented" message)
- Live market-data ingestion (sample universe data is used for seeded companies)
- PostgreSQL (currently SQLite; same ORM code, swap `DATABASE_URL` later)
- React frontend (Streamlit for now)

---

## Setup

```bash
# 1. Create a virtual environment
python -m venv .venv
.venv\Scripts\activate         # Windows PowerShell

# 2. Install dependencies
pip install -r requirements.txt
```

## Running the project

You need **two terminals** — the API backend and the Streamlit frontend.

**Terminal 1 — start the API:**
```bash
python -m uvicorn api.main:app --reload --port 8000
```
Visit `http://localhost:8000/docs` for interactive API docs (Swagger UI) —
useful for testing endpoints directly without the UI.

**Terminal 2 — start the dashboard:**
```bash
python -m streamlit run frontend/app.py
```
This opens `http://localhost:8501` in your browser.

## Testing

Run the Phase 1 unit tests (no PDF required — tests the parsing/calculation
logic directly):
```bash
python -m pytest tests -v
```

**Testing with a real PDF** (recommended next step, see PROJECT_CONTEXT.md §8):
1. Start both servers above.
2. In the Streamlit UI, upload a real annual report PDF.
3. Click "Run Extraction" — check how many metrics were found and whether the
   confidence scores / source pages look right.
4. If few/no metrics are found, open `extraction/financial_extractor.py` and
   add/adjust regex patterns to match that report's exact wording (e.g. some
   reports say "Total revenues" plural, or put numbers in a separate table
   column your pattern isn't catching).
5. Click "Compute Ratios" — check the validation warnings section for any
   flagged inconsistencies.
6. Set investment preferences and click "Get Recommendation" — check the
   explanation only references numbers you can see in the metrics table.

## Project structure

See `PROJECT_CONTEXT.md` §5 for the annotated folder structure and what each
module is responsible for.

## Quick demonstration

1. Start the API and the Streamlit dashboard in separate terminals.
2. In the dashboard, select **Quick Seed Sample Universe (5 Companies)**.
3. Explore peer benchmarks and clusters, then configure preferences in the
   Recommendation Studio to generate ranked, traceable recommendations.
