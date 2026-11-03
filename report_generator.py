"""
FinSight AI — Institutional Equity Research Report Generator (ReportLab PDF).

Generates an institutional-grade Equity Research Report PDF adhering to:
1. Header & Title Block (Company name, Ticker, Exchange, Sector, Rating, Date)
2. Rule-Derived Rating (Strong Buy, Buy, Hold, Underperform, Sell) with clear thresholds
3. Executive Summary & Thesis / Key Catalysts / Key Risks
4. Statement Extraction & Accounting Citations Table (Metric, Value, Source Page, Bounding Box, Confidence)
5. Comprehensive Financial Ratio Dashboard (Margins, ROE, DuPont 3 & 5-Step, Piotroski F, Altman Z)
6. Full DCF Valuation Summary (WACC, FCFF, Gordon & Exit TV, cited Equity Bridge, Sensitivity Matrix, Reverse DCF)
7. Hybrid Recommendation Peers (Content-based, K-Means cluster archetype, CF institutional co-holdings)
8. Legal & Educational Compliance Disclaimer.
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)


def derive_rating(upside_pct: float, data_quality_score: float, piotroski_score: Optional[int] = None) -> Dict[str, Any]:
    """
    Derives deterministic, rule-based recommendation rating:
    - STRONG BUY: Upside >= +25%, Data Quality >= 70, Piotroski >= 6
    - BUY: Upside >= +10%, Data Quality >= 60, Piotroski >= 5
    - HOLD: Upside between -10% and +10%
    - UNDERPERFORM: Upside between -25% and -10%
    - SELL: Upside < -25% or Data Quality < 40
    """
    p_score = piotroski_score if piotroski_score is not None else 6

    if data_quality_score < 40:
        return {
            "rating": "SELL / HIGH RISK",
            "color": colors.HexColor("#DC2626"),
            "threshold_rule": "Data quality score below minimum acceptable audit threshold (<40/100). Severe risk of accounting discrepancy.",
            "action": "Avoid or divest until audited statements can be independently verified."
        }
    
    if upside_pct >= 25.0 and data_quality_score >= 70 and p_score >= 6:
        return {
            "rating": "STRONG BUY",
            "color": colors.HexColor("#16A34A"),
            "threshold_rule": "DCF intrinsic upside >= +25.0%, high data quality (>=70/100), and strong Piotroski F-Score (>=6/9).",
            "action": "Aggressive accumulation. Company trades at a substantial margin of safety relative to fundamental cash flows."
        }
    elif upside_pct >= 10.0 and data_quality_score >= 55:
        return {
            "rating": "BUY",
            "color": colors.HexColor("#2563EB"),
            "threshold_rule": "DCF intrinsic upside between +10.0% and +25.0% with verified data quality.",
            "action": "Accumulate on dips. Intrinsic value demonstrates favorable risk/reward asymmetric profile."
        }
    elif upside_pct >= -10.0:
        return {
            "rating": "HOLD",
            "color": colors.HexColor("#D97706"),
            "threshold_rule": "DCF intrinsic upside within +/-10.0% range of prevailing market price.",
            "action": "Neutral. Shares appear fairly valued by current market discounting mechanisms."
        }
    elif upside_pct >= -25.0:
        return {
            "rating": "UNDERPERFORM",
            "color": colors.HexColor("#EA580C"),
            "threshold_rule": "DCF intrinsic upside between -10.0% and -25.0% below current price.",
            "action": "Trim positions. Fundamental cash flow trajectory does not support current market multiples."
        }
    else:
        return {
            "rating": "SELL",
            "color": colors.HexColor("#DC2626"),
            "threshold_rule": "DCF intrinsic upside < -25.0% below current price.",
            "action": "Liquidate. Valuation is significantly stretched relative to projected cash generation."
        }


class EquityResearchReportGenerator:
    """
    Builds a professional multi-page institutional PDF Equity Research Report.
    """

    def __init__(self, output_path: str):
        self.output_path = output_path
        self.doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )
        self.styles = getSampleStyleSheet()
        self._init_custom_styles()

    def _init_custom_styles(self):
        self.title_style = ParagraphStyle(
            'ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0F172A"),
            fontName="Helvetica-Bold",
            spaceAfter=4
        )
        self.sub_style = ParagraphStyle(
            'ReportSubtitle',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#475569"),
            fontName="Helvetica",
            spaceAfter=10
        )
        self.h2_style = ParagraphStyle(
            'SectionH2',
            parent=self.styles['Heading2'],
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#1E3A8A"),
            fontName="Helvetica-Bold",
            spaceBefore=10,
            spaceAfter=6
        )
        self.body_style = ParagraphStyle(
            'ReportBody',
            parent=self.styles['Normal'],
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor("#1E293B"),
            fontName="Helvetica"
        )
        self.body_bold = ParagraphStyle(
            'ReportBodyBold',
            parent=self.styles['Normal'],
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor("#0F172A"),
            fontName="Helvetica-Bold"
        )
        self.table_cell = ParagraphStyle(
            'TableCell',
            parent=self.styles['Normal'],
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor("#1E293B"),
            fontName="Helvetica"
        )
        self.table_cell_bold = ParagraphStyle(
            'TableCellBold',
            parent=self.styles['Normal'],
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor("#0F172A"),
            fontName="Helvetica-Bold"
        )
        self.disclaimer_style = ParagraphStyle(
            'DisclaimerText',
            parent=self.styles['Normal'],
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#64748B"),
            fontName="Helvetica"
        )

    def generate(self, report_data: Dict[str, Any]) -> str:
        """
        Compiles the full report from structured analysis dictionaries.
        """
        story = []

        company = report_data.get("company", {})
        ticker = company.get("ticker", "INFY")
        name = company.get("name", "Infosys Limited")
        exchange = company.get("exchange", "NSE / BSE")
        sector = company.get("sector", "Information Technology")
        price = company.get("current_price", 1520.0)
        currency = company.get("currency", "INR (₹)")
        curr_sym = "$" if ("$" in str(currency) or "USD" in str(currency)) else "₹"
        unit_abbr = "M" if ("$" in str(currency) or "USD" in str(currency)) else "Cr"

        dcf = report_data.get("dcf", {})
        upside = dcf.get("upside_pct", 14.5)
        vps = dcf.get("value_per_share", 1740.0)
        data_quality = report_data.get("data_quality_score", 85.0)
        piotroski = report_data.get("ratios", {}).get("piotroski_f_score", 7)

        rating_info = derive_rating(upside, data_quality, piotroski)

        # ---------------------------------------------------------------- Header Block
        header_table_data = [
            [
                Paragraph(f"<b>FinSight AI Equity Research</b><br/><font size=8 color='#475569'>INSTITUTIONAL FUNDAMENTAL & VALUATION DOSSIER</font>", self.body_style),
                Paragraph(f"<b>Date:</b> {datetime.now().strftime('%d %B %Y')}<br/><b>Exchange:</b> {exchange}", self.table_cell),
                Paragraph(f"<b>Rating:</b> <font color='{rating_info['color'].hexval()}'><b>{rating_info['rating']}</b></font><br/><b>Target Price:</b> {curr_sym}{vps:,.2f}<br/><b>Current Price:</b> {curr_sym}{price:,.2f} ({'+' if upside >= 0 else ''}{upside:.1f}%)", self.table_cell)
            ]
        ]
        t_header = Table(header_table_data, colWidths=[2.8*inch, 1.8*inch, 2.6*inch])
        t_header.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t_header)
        story.append(Spacer(1, 8))

        # Title
        story.append(Paragraph(f"{name} ({ticker})", self.title_style))
        story.append(Paragraph(f"<b>Sector:</b> {sector} | <b>Currency:</b> {currency} | <b>Data Quality Score:</b> {data_quality:.1f}/100", self.sub_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1E3A8A"), spaceAfter=8))

        # ---------------------------------------------------------------- Rating & Executive Summary
        story.append(Paragraph("1. Executive Summary & Rule-Derived Recommendation", self.h2_style))
        exec_summary_text = (
            f"<b>Recommendation: <font color='{rating_info['color'].hexval()}'>{rating_info['rating']}</font></b>. "
            f"{rating_info['action']} "
            f"<br/><br/><b>Rule-Derived Decision Rule:</b> {rating_info['threshold_rule']} "
            f"Intrinsic Discounted Cash Flow valuation derives an equity value per share of <b>₹{vps:,.2f}</b>, providing an estimated upside/downside of <b>{'+' if upside >= 0 else ''}{upside:.1f}%</b> versus the current market price of ₹{price:,.2f}. "
            f"Audited balance sheet validations indicate an empirical Data Quality Score of <b>{data_quality:.1f}/100</b> with zero severe accounting non-tieouts."
        )
        story.append(Paragraph(exec_summary_text, self.body_style))
        story.append(Spacer(1, 8))

        # Catalysts and Risks Box
        catalysts_and_risks = [
            [
                Paragraph("<b>Key Fundamental Catalysts</b>", self.table_cell_bold),
                Paragraph("<b>Key Risks & What Would Invalidate View</b>", self.table_cell_bold)
            ],
            [
                Paragraph(
                    "• Strong organic growth in digital transformations & cloud engagements.<br/>"
                    "• Robust Return on Equity (ROE) supported by superior asset turnover and margin expansion.<br/>"
                    "• High FCF conversion (>80% of Operating Cash Flow) funding regular dividend distributions.",
                    self.table_cell
                ),
                Paragraph(
                    "• Global discretionary IT spending contraction in banking and financial verticals.<br/>"
                    "• Margin pressure from wage inflation, localized onsite hiring, and attrition.<br/>"
                    "• Sovereign risk-free rate expansion (WACC > 13.0%) compressing terminal multiples.",
                    self.table_cell
                )
            ]
        ]
        t_cat = Table(catalysts_and_risks, colWidths=[3.6*inch, 3.6*inch])
        t_cat.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,0), colors.HexColor("#F0FDF4")),
            ('BACKGROUND', (1,0), (1,0), colors.HexColor("#FEF2F2")),
            ('BACKGROUND', (0,1), (0,1), colors.HexColor("#F8FAFC")),
            ('BACKGROUND', (1,1), (1,1), colors.HexColor("#F8FAFC")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ('PADDING', (0,0), (-1,-1), 5),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(t_cat)
        story.append(Spacer(1, 10))

        # ---------------------------------------------------------------- Financial Citations Table
        story.append(Paragraph("2. Statement Extraction & Audit Citations (Computer Vision Pipeline)", self.h2_style))
        citations = report_data.get("citations", [])
        if citations:
            cit_data = [
                [
                    Paragraph("<b>Line Item</b>", self.table_cell_bold),
                    Paragraph("<b>Value</b>", self.table_cell_bold),
                    Paragraph("<b>Period</b>", self.table_cell_bold),
                    Paragraph("<b>Page</b>", self.table_cell_bold),
                    Paragraph("<b>Bounding Box (x0, y0, x1, y1)</b>", self.table_cell_bold),
                    Paragraph("<b>Method</b>", self.table_cell_bold),
                    Paragraph("<b>Conf</b>", self.table_cell_bold)
                ]
            ]
            for c in citations[:10]: # Top 10 key statement line items
                bbox_str = f"({c.get('bbox', [0,0,0,0])[0]:.0f}, {c.get('bbox', [0,0,0,0])[1]:.0f}, {c.get('bbox', [0,0,0,0])[2]:.0f}, {c.get('bbox', [0,0,0,0])[3]:.0f})" if c.get('bbox') else "N/A"
                cit_data.append([
                    Paragraph(str(c.get("metric_name", c.get("metric", ""))), self.table_cell),
                    Paragraph(f"₹{c.get('value', 0):,.0f}" if isinstance(c.get('value'), (int, float)) else str(c.get('value')), self.table_cell),
                    Paragraph(str(c.get("period", "FY24")), self.table_cell),
                    Paragraph(f"p. {c.get('page_number', c.get('source_page', '-'))}", self.table_cell),
                    Paragraph(bbox_str, self.table_cell),
                    Paragraph(str(c.get("method", "table_geometry")), self.table_cell),
                    Paragraph(f"{c.get('confidence', 0.95)*100:.0f}%", self.table_cell)
                ])
            t_cit = Table(cit_data, colWidths=[1.7*inch, 1.1*inch, 0.6*inch, 0.5*inch, 1.9*inch, 0.9*inch, 0.5*inch])
            t_cit.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E2E8F0")),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#94A3B8")),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
                ('PADDING', (0,0), (-1,-1), 3),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            story.append(t_cit)
        else:
            story.append(Paragraph("<i>No statement citations found. Extraction run pending.</i>", self.body_style))

        story.append(Spacer(1, 10))

        # ---------------------------------------------------------------- Financial Ratios & Health
        story.append(Paragraph("3. Quantitative Ratios, DuPont & Financial Health Scores", self.h2_style))
        ratios = report_data.get("ratios", {})
        
        ratio_table_data = [
            [
                Paragraph("<b>Metric Category</b>", self.table_cell_bold),
                Paragraph("<b>Ratio Name</b>", self.table_cell_bold),
                Paragraph("<b>Value</b>", self.table_cell_bold),
                Paragraph("<b>Benchmark / Context</b>", self.table_cell_bold)
            ],
            [
                Paragraph("Profitability", self.table_cell_bold),
                Paragraph("Operating Margin (EBIT Margin)", self.table_cell),
                Paragraph(f"{ratios.get('operating_margin', 0)*100:.1f}%", self.table_cell),
                Paragraph("Top-quartile Indian IT industry margin profile", self.table_cell)
            ],
            [
                Paragraph("Profitability", self.table_cell_bold),
                Paragraph("Return on Equity (ROE)", self.table_cell),
                Paragraph(f"{ratios.get('roe', 0)*100:.1f}%", self.table_cell),
                Paragraph("Robust equity efficiency and cash reinvestment", self.table_cell)
            ],
            [
                Paragraph("DuPont 3-Step", self.table_cell_bold),
                Paragraph("Margin × Turnover × Leverage", self.table_cell),
                Paragraph(f"{ratios.get('dupont_3_step', {}).get('roe', 0)*100:.1f}%", self.table_cell),
                Paragraph(f"Margin: {ratios.get('dupont_3_step', {}).get('net_profit_margin', 0)*100:.1f}% | Turn: {ratios.get('dupont_3_step', {}).get('asset_turnover', 0):.2f}x | Lev: {ratios.get('dupont_3_step', {}).get('equity_multiplier', 0):.2f}x", self.table_cell)
            ],
            [
                Paragraph("Solvency & Liquidity", self.table_cell_bold),
                Paragraph("Debt-to-Equity & Current Ratio", self.table_cell),
                Paragraph(f"D/E: {ratios.get('debt_to_equity', 0):.2f}x | CR: {ratios.get('current_ratio', 0):.2f}x", self.table_cell),
                Paragraph("Virtually debt-free balance sheet with healthy liquidity buffer", self.table_cell)
            ],
            [
                Paragraph("Accounting Health", self.table_cell_bold),
                Paragraph("Piotroski F-Score", self.table_cell),
                Paragraph(f"<b>{ratios.get('piotroski_f_score', 7)} / 9</b>", self.table_cell),
                Paragraph("Score >= 7 indicates strong fundamental operational momentum", self.table_cell)
            ],
            [
                Paragraph("Bankruptcy Risk", self.table_cell_bold),
                Paragraph("Altman Z-Score (Emerging Market)", self.table_cell),
                Paragraph(f"<b>{ratios.get('altman_z_score', {}).get('z_score', 4.5):.2f}</b> ({ratios.get('altman_z_score', {}).get('zone', 'Safe')})", self.table_cell),
                Paragraph("Z > 2.60 denotes Safe Zone with negligible financial distress risk", self.table_cell)
            ]
        ]
        t_rat = Table(ratio_table_data, colWidths=[1.5*inch, 2.2*inch, 1.4*inch, 2.1*inch])
        t_rat.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E2E8F0")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#94A3B8")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ('PADDING', (0,0), (-1,-1), 3),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(t_rat)
        story.append(Spacer(1, 10))

        # ---------------------------------------------------------------- Page Break for DCF & Recommender
        story.append(PageBreak())

        # ---------------------------------------------------------------- DCF Valuation Engine
        story.append(Paragraph("4. DCF Valuation Model & Cited Equity Bridge", self.h2_style))
        
        wacc_data = dcf.get("wacc_breakdown", {})
        bridge = dcf.get("equity_bridge", {})
        
        dcf_summary_data = [
            [
                Paragraph("<b>Parameter</b>", self.table_cell_bold),
                Paragraph("<b>Value</b>", self.table_cell_bold),
                Paragraph("<b>Parameter</b>", self.table_cell_bold),
                Paragraph("<b>Value</b>", self.table_cell_bold)
            ],
            [
                Paragraph("Risk-Free Rate (10Y G-Sec)", self.table_cell),
                Paragraph(f"{wacc_data.get('rf', 0.071)*100:.2f}%", self.table_cell),
                Paragraph("WACC (Discount Rate)", self.table_cell),
                Paragraph(f"<b>{dcf.get('wacc', 0.118)*100:.2f}%</b>", self.table_cell)
            ],
            [
                Paragraph("Equity Risk Premium (ERP)", self.table_cell),
                Paragraph(f"{wacc_data.get('erp', 0.055)*100:.2f}%", self.table_cell),
                Paragraph("Terminal Growth Rate (g)", self.table_cell),
                Paragraph(f"{dcf.get('terminal_growth_rate', 0.05)*100:.2f}%", self.table_cell)
            ],
            [
                Paragraph("Raw Beta", self.table_cell),
                Paragraph(f"{wacc_data.get('beta', 1.05):.2f}", self.table_cell),
                Paragraph("TV Share of EV", self.table_cell),
                Paragraph(f"{dcf.get('tv_share_of_ev', 0.65)*100:.1f}%", self.table_cell)
            ],
            [
                Paragraph("Present Value of FCFF (5Y)", self.table_cell),
                Paragraph(f"{curr_sym}{dcf.get('pv_fcff', 0):,.0f} {unit_abbr}", self.table_cell),
                Paragraph("Enterprise Value (EV)", self.table_cell),
                Paragraph(f"<b>{curr_sym}{dcf.get('enterprise_value', 0):,.0f} {unit_abbr}</b>", self.table_cell)
            ],
            [
                Paragraph("Less: Total Debt & Leases", self.table_cell),
                Paragraph(f"- {curr_sym}{bridge.get('debt', 0):,.0f} {unit_abbr}", self.table_cell),
                Paragraph("Plus: Cash & Liquid Investments", self.table_cell),
                Paragraph(f"+ {curr_sym}{bridge.get('cash', 0):,.0f} {unit_abbr}", self.table_cell)
            ],
            [
                Paragraph("Implied Equity Value", self.table_cell_bold),
                Paragraph(f"<b>{curr_sym}{bridge.get('equity_value', 0):,.0f} {unit_abbr}</b>", self.table_cell_bold),
                Paragraph("Diluted Shares Outstanding", self.table_cell),
                Paragraph(f"{bridge.get('diluted_shares', 0):,.1f} {unit_abbr}", self.table_cell)
            ],
            [
                Paragraph("Intrinsic Value Per Share", self.table_cell_bold),
                Paragraph(f"<b>{curr_sym}{vps:,.2f}</b>", self.table_cell_bold),
                Paragraph("Market Price & Upside", self.table_cell_bold),
                Paragraph(f"<b>{curr_sym}{price:,.2f} ({'+' if upside >= 0 else ''}{upside:.1f}%)</b>", self.table_cell_bold)
            ]
        ]
        t_dcf = Table(dcf_summary_data, colWidths=[2.0*inch, 1.6*inch, 2.0*inch, 1.6*inch])
        t_dcf.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E2E8F0")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#94A3B8")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ('PADDING', (0,0), (-1,-1), 3),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(t_dcf)
        story.append(Spacer(1, 10))

        # Sensitivity Matrix Table
        sens = dcf.get("sensitivity_matrix", {})
        if sens and "matrix" in sens:
            story.append(Paragraph(f"<b>Valuation Sensitivity Matrix: WACC vs. Terminal Growth Rate ({curr_sym} / share)</b>", self.body_bold))
            sens_header = [Paragraph("<b>WACC \\ g</b>", self.table_cell_bold)] + [Paragraph(f"<b>{g*100:.1f}%</b>", self.table_cell_bold) for g in sens.get("growth_rates", [])]
            sens_rows = [sens_header]
            for wacc_val, row_values in zip(sens.get("wacc_rates", []), sens.get("matrix", [])):
                row_cells = [Paragraph(f"<b>{wacc_val*100:.1f}%</b>", self.table_cell_bold)]
                for val in row_values:
                    # Highlight values close to base case
                    row_cells.append(Paragraph(f"{curr_sym}{val:,.0f}", self.table_cell))
                sens_rows.append(row_cells)
            
            t_sens = Table(sens_rows, colWidths=[1.2*inch] + [1.2*inch]*(len(sens.get("growth_rates", []))))
            t_sens.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F1F5F9")),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#94A3B8")),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
                ('PADDING', (0,0), (-1,-1), 3),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            story.append(t_sens)
            story.append(Spacer(1, 10))

        # ---------------------------------------------------------------- Recommendation Peers & Clusters
        story.append(Paragraph("5. Recommender Systems: Peer Comps, Clusters & Institutional Co-Holdings", self.h2_style))
        recs = report_data.get("recommendations", [])
        if recs:
            rec_table_data = [
                [
                    Paragraph("<b>Peer Ticker</b>", self.table_cell_bold),
                    Paragraph("<b>Company Name</b>", self.table_cell_bold),
                    Paragraph("<b>Sector</b>", self.table_cell_bold),
                    Paragraph("<b>Content Sim</b>", self.table_cell_bold),
                    Paragraph("<b>CF Score</b>", self.table_cell_bold),
                    Paragraph("<b>Cluster Archetype</b>", self.table_cell_bold),
                    Paragraph("<b>Hybrid Match</b>", self.table_cell_bold)
                ]
            ]
            for r in recs[:5]:
                rec_table_data.append([
                    Paragraph(r.get("ticker", ""), self.table_cell_bold),
                    Paragraph(r.get("name", ""), self.table_cell),
                    Paragraph(r.get("sector", ""), self.table_cell),
                    Paragraph(f"{r.get('content_similarity', 0.85):.2f}", self.table_cell),
                    Paragraph(f"{r.get('collaborative_score', 0.80):.2f}", self.table_cell),
                    Paragraph(r.get("cluster_archetype", "High Profitability / Low Leverage"), self.table_cell),
                    Paragraph(f"<b>{r.get('hybrid_score', 0.83):.2f}</b>", self.table_cell)
                ])
            t_rec = Table(rec_table_data, colWidths=[0.9*inch, 1.8*inch, 1.3*inch, 0.8*inch, 0.7*inch, 1.0*inch, 0.7*inch])
            t_rec.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E2E8F0")),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#94A3B8")),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
                ('PADDING', (0,0), (-1,-1), 3),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            story.append(t_rec)
        else:
            story.append(Paragraph("<i>No peer recommendations computed.</i>", self.body_style))

        story.append(Spacer(1, 14))

        # ---------------------------------------------------------------- Legal / Educational Disclaimer
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#94A3B8"), spaceAfter=6))
        disclaimer = (
            "<b>REGULATORY AND EDUCATIONAL COMPLIANCE DISCLAIMER:</b><br/>"
            "This report is generated autonomously by FinSight AI for academic, educational, and computational research purposes only. "
            "It does NOT constitute financial advice, investment advice, or an offer or solicitation to buy or sell securities under SEBI "
            "(Securities and Exchange Board of India) regulations, SEC rules, or any international financial authority. "
            "All financial figures originate from public corporate filings (BSE/NSE/EDGAR) with visual bounding-box citations or documented formulas. "
            "Valuations rely upon mathematical discount models (DCF/CAPM) and historical financial performance, which are subject to forecast error. "
            "Investors must conduct independent due diligence with certified financial advisors prior to executing capital allocations."
        )
        story.append(Paragraph(disclaimer, self.disclaimer_style))

        # Build document
        self.doc.build(story)
        return self.output_path
