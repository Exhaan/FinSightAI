# Original Project Specification (verbatim)

I want you to help me design and build a complete academic project called:

FINANCIAL DOCUMENT INTELLIGENCE & INVESTMENT RECOMMENDATION SYSTEM

Alternative product name: FinSight AI — Financial Document Intelligence and Investment Recommendation Platform

This is a serious college project combining Computer Vision / Document Intelligence, Financial Analytics, Machine Learning, Recommendation Systems, and Explainable AI. I do NOT want a generic chatbot or a simple PDF summarizer.

The system should take corporate financial documents, extract structured financial information, calculate financial metrics, analyze companies, and generate personalized and explainable investment recommendations.

## 1. Project Overview
Transforms unstructured corporate financial documents (Annual Reports, Quarterly Reports, Earnings Reports, Financial Statements, Investor Presentations, Sustainability/ESG Reports) into structured financial intelligence. Evaluates companies on Revenue/growth, Profitability, Financial health, Financial leverage, Valuation, Market risk, ESG performance, User investment preferences. Generates explainable recommendations — the user must understand WHY a company was recommended.

## 2. Problem Statement
Corporate financial reports are hundreds of pages, with important info in Income Statements, Balance Sheets, Cash Flow Statements, MD&A, Risk Factors, Notes, ESG sections, Governance sections, Investor Presentations. Investors spend significant time manually locating/interpreting this. Goal: automate extraction/structuring, then use it for analytics and personalized recommendations.

## 3. Main Objective
Develop an AI-driven financial intelligence platform combining financial performance, growth, profitability, valuation, financial health, market risk, ESG metrics, and investor preferences to generate personalized and explainable investment recommendations.

## 4. High-Level Architecture
Corporate Financial Documents → Document Upload Module → PDF Processing → OCR + Layout Detection → Text Extraction + Table Extraction → Financial Information Extraction → Structured Financial Database → Feature Engineering → Financial Analytics Engine → Hybrid Recommendation Engine → Explainable AI Layer → Dashboard / UI

## 5. Module 1 — Document Upload
Accept PDF Annual/Quarterly/Earnings Reports, Financial Statements, Investor Presentations, ESG Reports. Validate file type, size, readability, page count. Initially focus on PDF.

## 6. Module 2 — PDF Processing
Load PDF; identify page count; attempt native text extraction; identify scanned/image pages; convert to images if OCR needed; OCR where required; detect layout; detect tables; detect headings/sections; store extracted content with metadata (document name, page number, section, extraction method, confidence score, raw content).

## 7. Module 3 — OCR and Document Intelligence
Support digital and scanned PDFs. Needs OCR, page segmentation, layout detection, table detection, heading detection, section identification. Suggested tools: PyMuPDF, pdfplumber, Tesseract OCR, PaddleOCR. Preferred logic: try native text extraction first; use OCR only when native extraction is unavailable/insufficient.

## 8. Document Structure Recognition
Identify/classify sections: Business Overview, MD&A, Income Statement, Balance Sheet, Cash Flow Statement, Risk Factors, Notes to Financial Statements, ESG/Sustainability, Corporate Governance. Use headings, layout, keywords, page structure.

## 9. Financial Information Extraction
**Income Statement:** Revenue, Cost of Revenue, Gross Profit, Operating Expenses, Operating Income, EBIT, EBITDA, Interest Expense, Tax Expense, Net Income, EPS.
**Balance Sheet:** Cash and Cash Equivalents, Current Assets, Total Assets, Current Liabilities, Total Liabilities, Short-Term Debt, Long-Term Debt, Total Debt, Shareholders' Equity.
**Cash Flow Statement:** Operating Cash Flow, CapEx, Free Cash Flow, Investing Cash Flow, Financing Cash Flow, Ending Cash Balance. FCF = Operating Cash Flow − CapEx.

## 10. Data Traceability
Every extracted metric retains source info, e.g.:
```json
{"metric": "Revenue", "value": 45000000000, "year": 2024, "source_page": 78,
 "document": "Annual_Report_2024.pdf", "extraction_method": "Table Extraction", "confidence": 0.94}
```

## 11. Data Validation
Extraction errors can arise from OCR errors, table extraction problems, different terminology, units (thousands/millions), bracketed negatives, multiple years in one table. Validation rules: Assets ≈ Liabilities + Equity; Gross Profit ≈ Revenue − Cost of Revenue; Free Cash Flow ≈ Operating Cash Flow − CapEx. Flag suspicious values rather than silently accepting them.

## 12. Database Design (PostgreSQL)
**COMPANIES:** company_id, company_name, ticker, sector, industry, market_cap.
**FINANCIAL_METRICS:** company_id, year, revenue, gross_profit, operating_income, net_income, assets, liabilities, equity, cash, debt, operating_cash_flow, capex, free_cash_flow, roe, roic.
**ESG_METRICS:** company_id, year, esg_score, environmental_score, social_score, governance_score.
**USER_PREFERENCES:** user_id, risk_tolerance, investment_style, investment_horizon, preferred_sector, minimum_esg_score, maximum_beta, maximum_debt_equity, minimum_roe, minimum_growth.

## 13. Feature Engineering
**Growth:** Revenue Growth = (Current − Previous)/Previous; Revenue CAGR = (End/Begin)^(1/years) − 1; Earnings Growth; EPS Growth; FCF Growth.
**Profitability:** Gross Margin = Gross Profit/Revenue; Operating Margin = Operating Income/Revenue; Net Margin = Net Income/Revenue; ROE; ROIC.
**Financial Health:** Debt-to-Equity = Total Debt/Shareholders' Equity; Debt-to-Assets; Current Ratio; Interest Coverage; Free Cash Flow.
**Valuation:** P/E, P/B, EV/EBITDA, Price-to-Sales, DCF Estimated Value, DCF Upside = (Intrinsic Value − Market Price)/Market Price.
**Market Risk:** Beta, Historical Volatility, Maximum Drawdown.
**ESG:** Overall, Environmental, Social, Governance scores.

## 14. Financial Feature Vector
[Revenue Growth, Revenue CAGR, ROE, ROIC, Operating Margin, Net Margin, FCF Growth, Debt-to-Equity, Current Ratio, P/E, EV/EBITDA, Beta, Volatility, ESG Score, DCF Upside]. Normalize before similarity/clustering (StandardScaler or MinMaxScaler — justify choice).

## 15. Hybrid Recommendation System
Not a single algorithm. Combine: Constraint-Based Filtering, Content-Based Recommendation, Weighted Financial Scoring, Cosine Similarity, K-Means Clustering.

## 16. Stage 1 — Hard Filters
Remove companies not meeting: Beta ≤ user max beta; Market Cap ≥ user min; Debt-to-Equity ≤ user max; ESG Score ≥ user min; Sector matches preference. Produces eligible company universe.

## 17. Stage 2 — Content-Based Recommendation
Represent each company as a feature vector; represent user preferences as an investment profile (style, risk tolerance, ESG preference, debt preference, sector, horizon). Engine finds companies best matching the profile.

## 18. Cosine Similarity
Cosine Similarity = (A·B)/(‖A‖‖B‖), computed between company vectors and user preference vector after normalization. Higher = better match.

## 19. Weighted Investment Score
Example weights (must be configurable, not hardcoded): 20% Growth + 20% Profitability + 15% Financial Health + 15% Valuation + 10% Market Risk + 10% ESG + 10% User Preference Match.

## 20. Category Scores
Growth Score (Revenue Growth, CAGR, EPS Growth, FCF Growth); Profitability Score (ROE, ROIC, Operating Margin, Net Margin); Financial Health Score (D/E, Current Ratio, Interest Coverage, FCF); Valuation Score (P/E, EV/EBITDA, P/B, P/S, DCF Upside); Risk Score (Beta, Volatility, Max Drawdown, Debt); ESG Score (E, S, G).

## 21. K-Means Clustering
Group companies with similar financial profiles (e.g. High Growth/High Risk; Stable/Large Cap; Value/Lower Valuation; High ESG; High Profitability). Not the sole recommender — a categorization layer. Choose k via Elbow Method / Silhouette Score.

## 22. Final Recommendation Pipeline
All Companies → Hard Filters → Eligible Companies → Feature Engineering → Category-Level Scores → Cosine Similarity → K-Means Cluster ID → Weighted Final Score → Final Ranking → Explainable Recommendation.

## 23. Explainable AI
Every recommendation explains why (e.g. "Revenue growth above threshold", "ROE strong vs peers", "Debt within risk tolerance", "ESG meets requirement") and lists risks (e.g. "High valuation", "Higher volatility", "Sector risk"). If an LLM is used, it must ONLY explain data/calculations already computed by the database — never invent figures, valuations, risks, or reasons.

## 24. User Preferences
Investment Style (Growth/Value/Income/Balanced); Risk Tolerance (Low/Medium/High); Investment Horizon (Short/Medium/Long-Term); Sector (Tech/Healthcare/Financials/Consumer/Energy/Industrials); Financial Filters (min ROE, max D/E, min revenue growth, max beta, min ESG); Valuation preference (Undervalued/Fairly Valued/High Growth).

## 25. Final Recommendation Output (example)
```
RANK #1 — NVIDIA
Investment Match Score: 91/100
Financial Profile: Growth: Excellent | Profitability: Excellent | Financial Health: Strong
                   Valuation: Expensive | Risk: Moderate to High | ESG: Good
WHY RECOMMENDED: Strong revenue growth; High profitability; Strong FCF; Strong match with growth profile
RISKS: High valuation; High volatility; Technology cycle sensitivity
```
Output must be based on actual calculated data.

## 26. Dashboard
Company Overview; Financial Performance; Financial Health; Risk; Valuation; ESG; Recommendation (Investment Match Score, Rank, Strengths, Risks, Explanation).

## 27. Technology Stack
Backend: Python, FastAPI. Document processing: PyMuPDF, pdfplumber. OCR: Tesseract or PaddleOCR. Table extraction: Camelot, pdfplumber. Data: Pandas, NumPy. ML: Scikit-learn (K-Means, Cosine Similarity, StandardScaler, MinMaxScaler). Database: PostgreSQL. MVP frontend: Streamlit. Potential production frontend: React.

## 28. Recommended Folder Structure
(see PROJECT_CONTEXT.md §5 for the as-built version — matches this closely, with `docs/` and `tests/` added and Postgres swapped for SQLite in the MVP.)

## 29. Minimum Viable Product
Input: Upload an Annual Report PDF. Extract: Revenue, Net Income, Assets, Debt, Equity, Operating Cash Flow, CapEx. Calculate: Revenue Growth, ROE, Debt-to-Equity, Free Cash Flow. Recommendation: user chooses Risk Tolerance, Investment Style, ESG Preference → return Ranked Companies, Investment Score, Recommendation Explanation.

## 30. Development Phases
1. Document Extraction (PDF Upload → Text → OCR → Table Extraction).
2. Financial Structuring (PostgreSQL DB, standardized metrics, validation, company-year datasets).
3. Financial Analytics (growth, profitability, financial health, risk, ESG calculations).
4. Recommendation System (Hard Filters, Category Scores, Weighted Scoring, Cosine Similarity, K-Means).
5. Explainability (reasons, strengths, risks, source-document traceability).
6. Dashboard (profiles, charts, ESG analysis, rankings, preference filters).

## 31. Evaluation
Document extraction: OCR Accuracy, Precision, Recall, F1, Table Extraction Accuracy. Recommendation quality: Precision@K, Ranking Quality, Similarity Score, User Preference Match. For an academic prototype, also: Case Studies, Manual Comparison, Expert Review.

## 32. Important Design Principles
Document extraction is the foundation, not the final project. Full pipeline: Financial Documents → Document Intelligence → Structured Financial Data → Financial Feature Engineering → Financial Analytics → Hybrid Recommendation Engine → Explainable Investment Insights.

## 33. Data Traceability Requirement
User should always be able to trace an extracted metric back to Original document, Page number, Extraction method. Treat as an important project feature, not an afterthought.

## 34. Final Project Positioning
Combines Computer Vision/Document Intelligence + OCR + NLP + Financial Analytics + Feature Engineering + Recommendation Systems + ML + Explainable AI. Demonstrates transforming unstructured corporate financial documents into structured financial intelligence, used to generate personalized, explainable investment insights.

## 35. Short Project Description
"Developing an AI-driven platform that extracts structured financial information from corporate reports and combines growth, profitability, valuation, risk, and ESG metrics with hybrid recommendation algorithms to generate personalized and explainable investment insights."

## 36. Expected Final Demonstration
User can: Upload Annual Report → system processes it → view extracted financial metrics → trace metrics to source pages → view calculated ratios → select investment preferences → receive ranked recommendations → understand why each company was recommended → view strengths and risks.

## 37. Development Instruction
Guide step-by-step with an actual working project, not just theory: final architecture, exact MVP scope, exact development order, required installs, complete folder structure, step-by-step implementation, code per module, run instructions, testing instructions after every major module, and clear explanations of why each algorithm is used. Do not move to the next phase until the previous phase is functional.

## 38. Final Development Order
PDF Upload → Native Text Extraction → OCR for Scanned Pages → Table Extraction → Financial Statement Identification → Financial Metric Extraction → Validation → Structured Database → Financial Ratios → Feature Engineering → Simple Company Ranking → Hard Filters → Weighted Scoring → Cosine Similarity → K-Means Clustering → Explainable Recommendations → Dashboard. First priority: a fully functioning end-to-end prototype, THEN improve extraction accuracy, table extraction, metric coverage, recommendation quality, explainability, UI, scalability.
