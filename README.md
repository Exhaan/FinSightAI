FinSightAI is an advanced, multi-modal financial intelligence and corporate valuation platform designed to ingest corporate filings, extract structured financial statements, perform automated discounted cash flow (DCF) and free cash flow to firm (FCFF) modeling, and generate comprehensive investment analysis reports.

Key Features
Universal Ingestion & OCR Engine: Parses complex financial PDF documents, annual reports, and corporate filings using specialized table and text extraction adapters.

Advanced Valuation Engines: Implements automated DCF (dcf.py, aesthetic_dcf.py) and FCFF (fcff_engine.py) models alongside WACC calculation (wacc_calculator.py) and ratio analysis (ratio_library.py).

Machine Learning & Intelligence: Features clustering, collaborative filtering, qualitative scoring (qualitative_scorer.py), and macro-regime analysis (macro_regime.py) to deliver robust insights.

Automated Report Generation: Compiles financial metrics, valuation outputs, and qualitative scores into polished investment reports (report_generator.py).

Robust Testing Suite: Extensively tested with pytest across ingestion, valuation, recommendation, and vision pipelines.


FinSightAI/
├── app.py                     # Main application interface / entry point
├── dcf_engine.py              # Discounted Cash Flow valuation engine
├── fcff_engine.py             # Free Cash Flow to Firm valuation engine
├── wacc_calculator.py         # Weighted Average Cost of Capital computations
├── financial_extractor.py     # Corporate filing statement extractor
├── ocr_engine.py              # OCR processing for scanned documents
├── report_generator.py        # Investment report synthesis and output
├── macro_regime.py            # Macroeconomic regime classification
└── requirements.txt           # Python package dependencies
