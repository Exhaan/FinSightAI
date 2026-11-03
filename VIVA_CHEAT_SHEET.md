# FinSight AI: Academic Defense & Viva Presentation Cheat-Sheet

This cheat-sheet provides concise, mathematically rigorous answers for defending FinSight AI across **Computer Vision (Document Intelligence)** and **Recommender Systems**.

---

## 1. Computer Vision & Document Intelligence Q&A

### Q1: Why did pdfplumber and traditional OCR fail on real Indian corporate filings (BSE / NSE)?
> **Answer:** Indian corporate annual reports prepared under **Ind AS Schedule III** use borderless, whitespace-aligned layout geometry. Traditional line-detection table tools (like Camelot or `pdfplumber.extract_tables()`) look for physical lines or rectangular grids, returning 0 tables. Furthermore, Indian numbering conventions (lakhs and crores formatted as `1,78,650`) break standard Western regex patterns (`\d{1,3}(,\d{3})+`). FinSight AI addresses this with `vision/table_layout.py`, which performs coordinate clustering with vertical line tolerance (`y_tolerance=6.0`), extracts column coordinate ranges, and tracks exact $(x_0, y_0, x_1, y_1)$ bounding boxes.

### Q2: How does the system handle scanned vs. digitally born PDF pages?
> **Answer:** FinSight AI implements a selective hybrid routing mechanism (`vision/ocr_engine.py`). Pages containing $\ge 20$ native text characters are processed via direct vector geometry extraction for speed and zero font degradation. Pages with $< 20$ characters are flagged as scanned and routed to the OCR engine (PaddleOCR with Tesseract fallback), capturing per-token bounding boxes and confidence scores.

### Q3: How do you guarantee zero LLM hallucinations in the extracted figures?
> **Answer:** All extraction is deterministic and audit-traceable. Every metric record contains:
> `(metric, value, period, unit_scale, source_page, bbox, extraction_method, confidence)`
> Downstream modules (Ratios, DCF, Reports) consume only cited figures that pass an empirical accounting audit ($\text{Assets} = \text{Liabilities} + \text{Equity}$; $\text{FCF} = \text{OCF} - \text{CapEx}$). If an LLM is used, it is restricted to polishing prose and forbidden from creating numerical outputs.

---

## 2. Quantitative Finance & Valuation Q&A

### Q4: How is WACC calculated for an Indian corporation?
> **Answer:** We compute $K_e$ via CAPM tailored to the Indian capital markets:
> $$K_e = R_f + \beta \times \text{ERP}$$
> where $R_f = 7.10\%$ (Indian Sovereign 10-Year G-Sec yield), and $\text{ERP} = 5.50\%$ (Emerging Market Equity Risk Premium for India). The after-tax cost of debt is $K_d = (I / D) \times (1 - t)$, and weights $(W_e, W_d)$ are computed using market capitalization and total debt.

### Q5: Explain the Equity Bridge in your DCF model.
> **Answer:** Enterprise Value ($\text{EV}$) represents the operating value of the firm ($\sum \text{PV}(\text{FCFF}) + \text{PV}(\text{Terminal Value})$). To arrive at Equity Value per share, we bridge from EV:
> $$\text{Equity Value} = \text{EV} - \text{Total Debt} - \text{Lease Liabilities} - \text{Preferred Stock} - \text{Minority Interest} + \text{Cash \& Liquid Investments}$$
> Dividing by diluted shares outstanding yields Intrinsic Value Per Share ($\text{VPS}$). Every component of the bridge is cited directly from the filing.

### Q6: What guardrails exist in your DCF valuation engine?
> **Answer:** 
> 1. If $\text{WACC} \le g$, the Gordon Growth formula denominator $\le 0$, which raises a `ValueError`.
> 2. If Terminal Value accounts for $>75\%$ of Enterprise Value, a model warning is flagged.
> 3. If projected FCFF is negative, an operational reinvestment warning is triggered.
> 4. Reverse DCF uses binary search to compute the exact growth rate implied by the current market price.

---

## 3. Recommender Systems Q&A

### Q7: How does your Hybrid Recommendation Engine combine Content-Based and Collaborative Filtering?
> **Answer:** We implement both a **weighted blend** and a **cascade model**:
> - **Content-Based:** 15-dimensional standardized financial ratio vectors (Profitability, Leverage, Growth, Liquidity) compared via Cosine Similarity.
> - **K-Means Clustering:** Centroid-derived archetype labeling (e.g., "High Profitability / Conservative Leverage") with automatic $k$-selection via Silhouette Score.
> - **Collaborative Filtering:** Uses institutional investment holdings (FII/DII co-holdings matrix) via Item-Item cosine similarity and Truncated SVD matrix factorization.
> - **Cold-Start Handling:** If an uploaded company has no institutional interactions, the recommender gracefully falls back to Content-Based peer similarities.

### Q8: How did you evaluate the recommender?
> **Answer:** We measure Top-K recommendations ($K=3, 5$) against institutional ground truth using:
> - **Precision@K** and **Recall@K**
> - **NDCG@K** (Normalized Discounted Cumulative Gain)
> - **Catalog Coverage** ($\% \text{ of universe recommended}$)
> - **Intra-List Diversity** (1 - average pairwise cosine similarity between recommended peers to avoid sector concentration).

---

## 4. Academic Contribution Summary

1. **Cross-Disciplinary Bridge:** Combines Document Intelligence (CV layout geometry, bounding-box traceability, accounting audit) with Financial Recommender Systems (Content + Cluster + Collaborative Filtering).
2. **Indian Market Grounding:** Complete support for BSE / NSE Ind AS Schedule III disclosures, sovereign yields, and institutional ownership patterns.
3. **Audit Integrity:** Zero-hallucination guarantee with empirical Data Quality Scoring and automated publication-grade Equity Research Reports.
