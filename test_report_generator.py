import os
import pytest
from reporting.report_generator import EquityResearchReportGenerator, derive_rating

def test_derive_rating_thresholds():
    # Strong Buy: upside >= 25%, dq >= 70, piotroski >= 6
    r1 = derive_rating(upside_pct=30.0, data_quality_score=85.0, piotroski_score=7)
    assert r1["rating"] == "STRONG BUY"

    # Buy: upside >= 10%, dq >= 55
    r2 = derive_rating(upside_pct=15.0, data_quality_score=65.0, piotroski_score=5)
    assert r2["rating"] == "BUY"

    # Hold: upside between -10% and +10%
    r3 = derive_rating(upside_pct=2.0, data_quality_score=80.0, piotroski_score=6)
    assert r3["rating"] == "HOLD"

    # Underperform: upside between -25% and -10%
    r4 = derive_rating(upside_pct=-18.0, data_quality_score=80.0, piotroski_score=6)
    assert r4["rating"] == "UNDERPERFORM"

    # Sell: upside < -25%
    r5 = derive_rating(upside_pct=-32.0, data_quality_score=80.0, piotroski_score=6)
    assert r5["rating"] == "SELL"

    # Sell / High Risk: low data quality (< 40)
    r6 = derive_rating(upside_pct=40.0, data_quality_score=35.0, piotroski_score=8)
    assert "SELL" in r6["rating"]


def test_equity_research_report_generation(tmp_path):
    out_pdf = str(tmp_path / "test_research_report.pdf")
    generator = EquityResearchReportGenerator(out_pdf)

    payload = {
        "company": {
            "ticker": "INFY",
            "name": "Infosys Limited",
            "exchange": "NSE / BSE",
            "sector": "Information Technology",
            "current_price": 1520.0,
            "currency": "INR (₹)"
        },
        "citations": [
            {
                "metric_name": "Revenue",
                "value": 178650.0,
                "period": "FY24",
                "page_number": 218,
                "bbox": [54.0, 110.0, 550.0, 125.0],
                "method": "table_geometry",
                "confidence": 0.95
            },
            {
                "metric_name": "Operating Income",
                "value": 37900.0,
                "period": "FY24",
                "page_number": 218,
                "bbox": [54.0, 240.0, 550.0, 255.0],
                "method": "table_geometry",
                "confidence": 0.95
            }
        ],
        "validation_report": {
            "data_quality_score": 88.0,
            "failures": []
        },
        "data_quality_score": 88.0,
        "ratios": {
            "operating_margin": 0.212,
            "roe": 0.301,
            "debt_to_equity": 0.08,
            "current_ratio": 2.15,
            "dupont_3_step": {
                "net_profit_margin": 0.165,
                "asset_turnover": 1.15,
                "equity_multiplier": 1.58,
                "roe": 0.301
            },
            "piotroski_f_score": 8,
            "altman_z_score": {
                "z_score": 4.82,
                "zone": "Safe"
            }
        },
        "dcf": {
            "wacc": 0.118,
            "terminal_growth_rate": 0.05,
            "pv_fcff": 95000.0,
            "enterprise_value": 620000.0,
            "value_per_share": 1740.0,
            "upside_pct": 14.5,
            "tv_share_of_ev": 0.68,
            "equity_bridge": {
                "debt": 8500.0,
                "cash": 14200.0,
                "equity_value": 625700.0,
                "diluted_shares": 359.5
            },
            "wacc_breakdown": {
                "rf": 0.071,
                "erp": 0.055,
                "beta": 1.05
            },
            "sensitivity_matrix": {
                "wacc_rates": [0.108, 0.118, 0.128],
                "growth_rates": [0.04, 0.05, 0.06],
                "matrix": [
                    [1850.0, 1990.0, 2180.0],
                    [1620.0, 1740.0, 1890.0],
                    [1440.0, 1530.0, 1650.0]
                ]
            }
        },
        "recommendations": [
            {
                "ticker": "TCS",
                "name": "Tata Consultancy Services Ltd",
                "sector": "Information Technology",
                "content_similarity": 0.94,
                "collaborative_score": 0.88,
                "cluster_archetype": "High Margin / Low Debt",
                "hybrid_score": 0.91
            }
        ]
    }

    res_path = generator.generate(payload)
    assert os.path.exists(res_path)
    assert os.path.getsize(res_path) > 1000
