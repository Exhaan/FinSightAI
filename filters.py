"""
Stage 1 — Hard Constraint Filtering Engine (spec §16).

Filters out companies that fail strict investor constraints:
- Maximum Beta (Market Risk)
- Minimum Market Cap
- Maximum Debt-to-Equity (Financial Leverage)
- Minimum ESG Score
- Sector Preference Alignment
- Minimum Return on Equity (ROE)
- Minimum Revenue Growth

Produces the eligible investment universe for downstream ranking.
"""


def passes_hard_filters(company_data: dict, preferences: dict) -> tuple[bool, list[str]]:
    """
    company_data: dict containing both computed ratios and company metadata
                  (debt_to_equity, roe, revenue_growth, beta, market_cap, esg_score, sector)
    preferences: user preference constraints
    Returns: (passes: bool, list_of_reasons_failed: list[str])
    """
    failures = []

    # 1. Debt-to-Equity Filter
    max_de = preferences.get("maximum_debt_equity")
    de = company_data.get("debt_to_equity")
    if max_de is not None and de is not None and de > max_de:
        failures.append(f"Debt-to-Equity ({de:.2f}) exceeds your maximum threshold of {max_de:.2f}.")

    # 2. Minimum ROE Filter
    min_roe = preferences.get("minimum_roe")
    roe_val = company_data.get("roe")
    if min_roe is not None and roe_val is not None and roe_val < min_roe:
        failures.append(f"Return on Equity ({roe_val:.1%}) is below your minimum threshold of {min_roe:.1%}.")

    # 3. Minimum Revenue Growth Filter
    min_growth = preferences.get("minimum_growth")
    growth = company_data.get("revenue_growth")
    if min_growth is not None and growth is not None and growth < min_growth:
        failures.append(f"Revenue Growth ({growth:.1%}) is below your minimum requirement of {min_growth:.1%}.")

    # 4. Maximum Beta (Market Risk)
    max_beta = preferences.get("maximum_beta")
    beta_val = company_data.get("beta")
    if max_beta is not None and beta_val is not None and beta_val > max_beta:
        failures.append(f"Beta ({beta_val:.2f}) exceeds your maximum risk tolerance of {max_beta:.2f}.")

    # 5. Minimum ESG Score
    min_esg = preferences.get("minimum_esg_score")
    esg_val = company_data.get("esg_score")
    if min_esg is not None and esg_val is not None and esg_val < min_esg:
        failures.append(f"ESG Score ({esg_val:.1f}) is below your minimum requirement of {min_esg:.1f}.")

    # 6. Minimum Market Cap
    min_mcap = preferences.get("minimum_market_cap")
    mcap_val = company_data.get("market_cap")
    if min_mcap is not None and mcap_val is not None and mcap_val < min_mcap:
        failures.append(f"Market Cap (${mcap_val:,.0f}M) is below your minimum size of ${min_mcap:,.0f}M.")

    # 7. Sector Preference
    pref_sector = preferences.get("preferred_sector")
    comp_sector = company_data.get("sector")
    if pref_sector and pref_sector not in ["All", "Any"] and comp_sector:
        if pref_sector.lower() != comp_sector.lower():
            failures.append(f"Sector '{comp_sector}' does not match your preference '{pref_sector}'.")

    return (len(failures) == 0, failures)
