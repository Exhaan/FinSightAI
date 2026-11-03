"""
Financial Feature Vector Engine (spec §14).

Constructs the standardized 15-dimensional financial feature vector for each company:
1. Revenue Growth
2. Revenue CAGR
3. ROE
4. ROIC
5. Operating Margin
6. Net Margin
7. FCF Growth
8. Debt-to-Equity
9. Current Ratio
10. P/E Ratio
11. EV/EBITDA
12. Beta
13. Volatility
14. ESG Score
15. DCF Upside

Includes normalization with scikit-learn (MinMaxScaler & StandardScaler) and vector distance utilities.
"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler

FEATURE_NAMES = [
    "revenue_growth",
    "revenue_cagr",
    "roe",
    "roic",
    "operating_margin",
    "net_margin",
    "fcf_growth",
    "debt_to_equity",
    "current_ratio",
    "pe_ratio",
    "ev_ebitda",
    "beta",
    "volatility",
    "esg_score",
    "dcf_upside",
]

# Reasonable default values for imputation when a specific ratio cannot be computed
DEFAULT_IMPUTE_VALUES = {
    "revenue_growth": 0.05,
    "revenue_cagr": 0.05,
    "roe": 0.12,
    "roic": 0.10,
    "operating_margin": 0.15,
    "net_margin": 0.10,
    "fcf_growth": 0.05,
    "debt_to_equity": 1.0,
    "current_ratio": 1.5,
    "pe_ratio": 22.0,
    "ev_ebitda": 15.0,
    "beta": 1.0,
    "volatility": 0.25,
    "esg_score": 75.0,
    "dcf_upside": 0.05,
}


def build_raw_feature_vector(ratios: dict) -> np.ndarray:
    """
    Extracts the 15-dimensional raw feature vector from a company's ratio dictionary.
    Missing values are imputed with neutral reference defaults.
    """
    vector = []
    for feat in FEATURE_NAMES:
        val = ratios.get(feat)
        if val is None or np.isnan(val) or np.isinf(val):
            val = DEFAULT_IMPUTE_VALUES[feat]
        vector.append(float(val))
    return np.array(vector, dtype=float)


def build_feature_dataframe(companies_ratios: dict[str, dict]) -> pd.DataFrame:
    """
    companies_ratios: {company_name: ratios_dict}
    Returns a pandas DataFrame indexed by company_name with 15 columns.
    """
    rows = []
    index = []
    for cname, ratios in companies_ratios.items():
        vec = build_raw_feature_vector(ratios)
        rows.append(vec)
        index.append(cname)

    df = pd.DataFrame(rows, index=index, columns=FEATURE_NAMES)
    return df


def normalize_feature_vectors(
    df: pd.DataFrame, method: str = "minmax"
) -> tuple[np.ndarray, object]:
    """
    Normalizes feature vectors across companies.
    method: 'minmax' (scales to [0, 1]) or 'standard' (mean 0, variance 1).
    Returns (normalized_array, scaler).
    """
    scaler = MinMaxScaler(feature_range=(0, 1)) if method == "minmax" else StandardScaler()
    
    # If only 1 company, minmax will return zeros; handle gracefully with default bounds
    if len(df) == 1:
        normalized = np.full(df.shape, 0.5)
    else:
        normalized = scaler.fit_transform(df)

    return normalized, scaler
