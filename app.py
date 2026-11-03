"""
FinSight AI — Comprehensive Financial Document Intelligence & Recommendation Dashboard (Phases 1–6).

Run with:
    streamlit run frontend/app.py
"""
import os
import streamlit as st
import requests
import pandas as pd
import numpy as np

API_URL = os.environ.get("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="FinSight AI — Financial Intelligence & Recommendations",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------------- Styling
st.markdown("""
<style>
    .main-title { font-size: 2.2rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0.2rem; }
    .sub-title { font-size: 1.05rem; color: #475569; margin-bottom: 1.5rem; }
    .metric-card { background-color: #F8FAFC; border-radius: 8px; padding: 15px; border-left: 5px solid #3B82F6; margin-bottom: 10px; }
    .strength-box { background-color: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 6px; padding: 12px; margin-bottom: 8px; }
    .risk-box { background-color: #FEF2F2; border: 1px solid #FECACA; border-radius: 6px; padding: 12px; margin-bottom: 8px; }
    .archetype-badge { background-color: #EEF2FF; color: #4338CA; padding: 4px 10px; border-radius: 12px; font-size: 0.85rem; font-weight: 600; display: inline-block; }
    
    /* Aesthetic DCF Calculator Design System (zi-cong-tan inspired) */
    .aesthetic-hero {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        gap: 14px;
        margin-bottom: 20px;
    }
    .aesthetic-stat {
        background: #F1F5F9;
        border-radius: 10px;
        padding: 16px 18px;
        border: 1px solid #CBD5E1;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .aesthetic-stat.main {
        background: linear-gradient(135deg, #0F766E 0%, #115E59 100%);
        color: #FFFFFF !important;
        border: 1px solid #0D9488;
    }
    .aesthetic-stat.main .lb, .aesthetic-stat.main .sub-text {
        color: #CCFBF1 !important;
    }
    .aesthetic-stat .lb {
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748B;
        margin-bottom: 4px;
    }
    .aesthetic-stat .val {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        line-height: 1.1;
        margin-bottom: 6px;
    }
    .aesthetic-stat .sub-text {
        font-size: 0.82rem;
        color: #64748B;
        font-weight: 500;
    }
    .text-green { color: #16A34A; font-weight: 700; }
    .text-red { color: #DC2626; font-weight: 700; }
    
    .waterfall-row {
        display: flex;
        justify-content: space-between;
        padding: 9px 0;
        border-bottom: 1px solid #E2E8F0;
        font-size: 0.92rem;
    }
    .waterfall-row.total-row {
        font-weight: 800;
        color: #0F172A;
        border-top: 2px solid #0F172A;
        border-bottom: 2px solid #0F172A;
        background-color: #F8FAFC;
        padding: 11px 8px;
        margin: 4px 0;
    }
    .lock-badge {
        display: inline-block;
        background-color: #E2E8F0;
        color: #475569;
        font-size: 0.75rem;
        padding: 2px 6px;
        border-radius: 4px;
        margin-right: 6px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------- Header
col_header, col_seed = st.columns([3, 1])
with col_header:
    st.markdown('<div class="main-title">📈 FinSight AI — Financial Document Intelligence Platform</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Automated PDF Statement Extraction • 15-Dim Feature Engineering • K-Means Clustering • Hybrid Explainable Recommendation Engine</div>', unsafe_allow_html=True)

with col_seed:
    st.write("")
    if st.button("🚀 Quick Seed Indian Universe (BSE & NSE)", type="primary", use_container_width=True):
        with st.spinner("Seeding database with Indian corporate reports (INFY, TCS, HDFCBANK, RELIANCE, ITC)..."):
            try:
                resp = requests.post(f"{API_URL}/companies/seed", timeout=60)
                if resp.ok:
                    st.success("Successfully seeded 5 company reports!")
                    st.rerun()
                else:
                    st.error(f"Seeding failed: {resp.text}")
            except Exception as e:
                st.error(f"Cannot connect to backend API at {API_URL}. Start it with `python -m uvicorn api.main:app --port 8000`.")

# ---------------------------------------------------------------- Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📄 1. Document Extraction & Traceability",
    "📊 2. Company Financial Intelligence",
    "🌐 3. Multi-Company Peer Benchmarking & Clusters",
    "🎯 4. Hybrid Recommendation & Explainability Studio",
    "📑 5. Institutional Equity Research Report & DCF"
])

# ==============================================================================
# TAB 1: Document Extraction & Traceability
# ==============================================================================
with tab1:
    st.header("Corporate Financial Report Upload & Information Extraction")
    col_up, col_info = st.columns([1, 1])

    # Document selector from database
    available_docs = []
    try:
        d_resp = requests.get(f"{API_URL}/documents", timeout=5)
        if d_resp.ok:
            available_docs = d_resp.json()
    except Exception:
        pass

    with col_up:
        uploaded_file = st.file_uploader("Upload Annual Report / 10-K / 10-Q (PDF)", type=["pdf"])
        if uploaded_file is not None:
            # Check if this file was already uploaded to avoid re-upload loop
            if st.session_state.get("last_uploaded_filename") != uploaded_file.name:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                try:
                    with st.spinner(f"Uploading '{uploaded_file.name}'..."):
                        resp = requests.post(f"{API_URL}/upload", files=files, timeout=60)
                        if resp.ok:
                            data = resp.json()
                            st.session_state.current_doc_id = data["document_id"]
                            st.session_state.current_filename = data["filename"]
                            st.session_state.last_uploaded_filename = uploaded_file.name
                            st.success(f"✓ Uploaded '{data['filename']}' ({data['num_pages']} pages). Assigned Document ID: {data['document_id']}")
                            # Automatically trigger extraction for newly uploaded file
                            with st.spinner(f"Auto-extracting metrics and balance sheets from {uploaded_file.name}..."):
                                ext_resp = requests.post(f"{API_URL}/extract/{data['document_id']}", timeout=120)
                                if ext_resp.ok:
                                    st.session_state.extraction_data = ext_resp.json()
                                    st.rerun()
                        else:
                            st.error(f"Upload error: {resp.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")

    with col_info:
        st.info("💡 **Traceability Guarantee**: Every extracted number retains its source page number, extraction method (native text / table geometry), and confidence score, ensuring 100% auditability without LLM hallucinations.")
        if available_docs:
            st.markdown("**📂 Pre-Ingested Indian Universe Reports:**")
            for d in available_docs[:5]:
                st.caption(f"• **Doc #{d['document_id']}**: {d['company_name']} ({d['ticker']}) — `{d['filename']}`")

    # If document is selected or loaded
    current_doc = st.session_state.get("current_doc_id", 1)

    st.divider()
    col_ctrl1, col_ctrl2 = st.columns([1, 2])
    with col_ctrl1:
        doc_options = {d["document_id"]: f"Doc #{d['document_id']}: {d['company_name']} ({d['ticker']}) - {d['filename']}" for d in available_docs} if available_docs else {1: "Doc #1"}
        selected_key = st.selectbox(
            "Select Document to Scan & Analyze",
            options=list(doc_options.keys()),
            format_func=lambda x: doc_options.get(x, f"Doc #{x}"),
            index=list(doc_options.keys()).index(current_doc) if current_doc in doc_options else 0
        )
        doc_id_input = selected_key
        extract_btn = st.button("🔍 Run Full Extraction Pipeline", type="primary", use_container_width=True)

    if extract_btn:
        with st.spinner("Classifying sections, parsing tables, and extracting metrics..."):
            try:
                resp = requests.post(f"{API_URL}/extract/{doc_id_input}", timeout=120)
                if resp.ok:
                    data = resp.json()
                    st.session_state.extraction_data = data
                    st.success(f"Extraction complete! Extracted {len(data['extracted_metrics'])} financial metrics across {data['num_pages']} pages.")
                else:
                    st.error(f"Extraction failed: {resp.text}")
            except Exception as e:
                st.error(f"Extraction request error: {e}")

    # Display Extracted Information
    if "extraction_data" in st.session_state:
        ext_data = st.session_state.extraction_data

        # Section Structure
        st.subheader("1. Identified Document Structure (spec §8)")
        sec_cols = st.columns(len(ext_data.get("sections", [])) or 1)
        for idx, sec in enumerate(ext_data.get("sections", [])):
            with sec_cols[idx % len(sec_cols)]:
                st.markdown(f"**Page {sec['page_number']}**\n\n`{sec['primary_section']}`")

        st.subheader("2. Structured Financial Metrics (with Full Traceability, spec §10)")
        metrics_list = ext_data.get("extracted_metrics", [])
        if metrics_list:
            df_metrics = pd.DataFrame(metrics_list)
            st.dataframe(
                df_metrics[[
                    "metric", "value", "year", "source_page", "extraction_method", "confidence", "raw_context"
                ]],
                use_container_width=True
            )
        else:
            st.warning("No metrics matched.")

        # Validation Checks & Financial Ratios
        st.subheader("3. Accounting Validation Rules & Computed Document Ratios")
        try:
            ratios_resp = requests.post(f"{API_URL}/ratios/{doc_id_input}", timeout=30)
            if ratios_resp.ok:
                r_data = ratios_resp.json()
                doc_ratios = r_data.get("ratios", {})
                
                # Display Key Ratios Card Grid
                col_r1, col_r2, col_r3, col_r4 = st.columns(4)
                with col_r1:
                    cr = doc_ratios.get("current_ratio")
                    st.metric("Current Ratio", f"{cr:.2f}x" if cr is not None else "N/A", help="Current Assets / Current Liabilities")
                with col_r2:
                    qr = doc_ratios.get("quick_ratio")
                    st.metric("Quick Ratio", f"{qr:.2f}x" if qr is not None else "N/A", help="(Current Assets - Inventories) / Current Liabilities")
                with col_r3:
                    al = doc_ratios.get("assets_to_liabilities")
                    st.metric("Assets upon Liabilities", f"{al:.2f}x" if al is not None else "N/A", help="Total Assets / Total Liabilities")
                with col_r4:
                    de = doc_ratios.get("debt_to_equity")
                    st.metric("Debt-to-Equity", f"{de:.2f}x" if de is not None else "N/A", help="Total Debt / Shareholders' Equity")

                col_r5, col_r6, col_r7, col_r8 = st.columns(4)
                with col_r5:
                    opm = doc_ratios.get("operating_margin")
                    st.metric("Operating Margin", f"{opm*100:.1f}%" if opm is not None else "N/A")
                with col_r6:
                    npm = doc_ratios.get("net_margin")
                    st.metric("Net Margin", f"{npm*100:.1f}%" if npm is not None else "N/A")
                with col_r7:
                    roe_val = doc_ratios.get("roe")
                    st.metric("Return on Equity", f"{roe_val*100:.1f}%" if roe_val is not None else "N/A")
                with col_r8:
                    fcf_val = doc_ratios.get("free_cash_flow")
                    st.metric("Free Cash Flow", f"₹{fcf_val:,.0f} Cr" if fcf_val is not None else "N/A")

                warnings = r_data.get("validation_warnings", [])
                if warnings:
                    for w in warnings:
                        st.warning(f"⚠ {w}")
                else:
                    st.success("✓ All accounting identities verified: Assets ≈ Liabilities + Equity | Gross Profit = Rev - COGS | FCF = OCF - CapEx.")
        except Exception as e:
            st.error(f"Could not compute ratios: {e}")


# ==============================================================================
# TAB 2: Company Financial Intelligence
# ==============================================================================
with tab2:
    st.header("Company Deep-Dive & 15-Dimensional Financial Profile")
    try:
        comp_resp = requests.get(f"{API_URL}/companies", timeout=10)
        if comp_resp.ok:
            companies = comp_resp.json()
            if companies:
                cnames = [c["company_name"] for c in companies]
                selected_company_name = st.selectbox("Select Company to Analyze", cnames)
                company_record = next(c for c in companies if c["company_name"] == selected_company_name)
                ratios = company_record.get("ratios", {})

                # Metric Cards Top Row
                c1, c2, c3, c4, c5 = st.columns(5)
                with c1:
                    st.metric("Sector", company_record.get("sector", "N/A"))
                with c2:
                    st.metric("Market Cap (₹ Cr)", f"₹{company_record.get('market_cap', 0):,.0f} Cr")
                with c3:
                    rg = ratios.get("revenue_growth")
                    st.metric("Revenue Growth", f"{rg:.1%}" if rg is not None else "N/A")
                with c4:
                    roe = ratios.get("roe")
                    st.metric("Return on Equity", f"{roe:.1%}" if roe is not None else "N/A")
                with c5:
                    fcf = ratios.get("free_cash_flow")
                    st.metric("Free Cash Flow", f"₹{fcf:,.0f} Cr" if fcf is not None else "N/A")

                st.divider()

                # Detailed Features Breakdown
                col_feat, col_radar = st.columns([1, 1])

                with col_feat:
                    st.subheader("Financial Ratios & Fundamental Features")
                    feat_data = [
                        {"Category": "Growth", "Feature": "Revenue Growth", "Value": f"{ratios.get('revenue_growth', 0):.1%}"},
                        {"Category": "Growth", "Feature": "Revenue CAGR", "Value": f"{ratios.get('revenue_cagr', 0):.1%}"},
                        {"Category": "Growth", "Feature": "FCF Growth", "Value": f"{ratios.get('fcf_growth', 0):.1%}" if ratios.get('fcf_growth') else "N/A"},
                        {"Category": "Profitability", "Feature": "Gross Margin", "Value": f"{ratios.get('gross_margin', 0):.1%}"},
                        {"Category": "Profitability", "Feature": "Operating Margin", "Value": f"{ratios.get('operating_margin', 0):.1%}"},
                        {"Category": "Profitability", "Feature": "Net Margin", "Value": f"{ratios.get('net_margin', 0):.1%}"},
                        {"Category": "Profitability", "Feature": "Return on Equity (ROE)", "Value": f"{ratios.get('roe', 0):.1%}"},
                        {"Category": "Profitability", "Feature": "Return on Invested Capital (ROIC)", "Value": f"{ratios.get('roic', 0):.1%}" if ratios.get('roic') else "N/A"},
                        {"Category": "Financial Health", "Feature": "Current Ratio", "Value": f"{ratios.get('current_ratio', 0):.2f}x" if ratios.get('current_ratio') else "N/A"},
                        {"Category": "Financial Health", "Feature": "Quick Ratio", "Value": f"{ratios.get('quick_ratio', 0):.2f}x" if ratios.get('quick_ratio') else "N/A"},
                        {"Category": "Financial Health", "Feature": "Assets upon Liabilities", "Value": f"{ratios.get('assets_to_liabilities', 0):.2f}x" if ratios.get('assets_to_liabilities') else "N/A"},
                        {"Category": "Financial Health", "Feature": "Debt-to-Equity", "Value": f"{ratios.get('debt_to_equity', 0):.2f}x"},
                        {"Category": "Valuation", "Feature": "P/E Ratio", "Value": f"{ratios.get('pe_ratio', 0):.1f}x" if ratios.get('pe_ratio') else "N/A"},
                        {"Category": "Valuation", "Feature": "EV / EBITDA", "Value": f"{ratios.get('ev_ebitda', 0):.1f}x" if ratios.get('ev_ebitda') else "N/A"},
                        {"Category": "Valuation", "Feature": "DCF Estimated Upside", "Value": f"{ratios.get('dcf_upside', 0):.1%}" if ratios.get('dcf_upside') else "N/A"},
                        {"Category": "Market Risk", "Feature": "Beta (NSE Sensitivity)", "Value": f"{ratios.get('beta', 1.0):.2f}"},
                        {"Category": "ESG (BRSR)", "Feature": "SEBI BRSR ESG Composite Score", "Value": f"{ratios.get('esg_score', 75):.1f}/100"},
                    ]
                    st.dataframe(pd.DataFrame(feat_data), use_container_width=True)

                with col_radar:
                    st.subheader("Category Performance Breakdown (spec §20)")
                    from analytics.scoring import compute_category_scores
                    cat_scores = compute_category_scores(ratios)

                    df_cats = pd.DataFrame([
                        {"Category": "Growth", "Score (0-100)": cat_scores["growth_score"]},
                        {"Category": "Profitability", "Score (0-100)": cat_scores["profitability_score"]},
                        {"Category": "Financial Health", "Score (0-100)": cat_scores["financial_health_score"]},
                        {"Category": "Valuation", "Score (0-100)": cat_scores["valuation_score"]},
                        {"Category": "Risk (Safety)", "Score (0-100)": cat_scores["risk_score"]},
                        {"Category": "ESG", "Score (0-100)": cat_scores["esg_score"]},
                    ])

                    st.bar_chart(df_cats.set_index("Category"))
            else:
                st.info("No companies found in database. Click 'Quick Seed Sample Universe' at the top to load sample reports.")
    except Exception as e:
        st.error(f"Could not load companies: {e}")


# ==============================================================================
# TAB 3: Multi-Company Peer Benchmarking & Clusters
# ==============================================================================
with tab3:
    st.header("Multi-Company Benchmarking & K-Means Clustering (spec §21)")

    try:
        comp_data_resp = requests.get(f"{API_URL}/compare", timeout=10)
        cluster_resp = requests.get(f"{API_URL}/clusters", timeout=10)

        if comp_data_resp.ok and cluster_resp.ok:
            comp_table = comp_data_resp.json()
            cluster_info = cluster_resp.json()

            st.subheader("1. Cross-Company Comparative Financial Table")
            df_comp = pd.DataFrame(comp_table)
            st.dataframe(df_comp, use_container_width=True)

            st.divider()

            col_pca, col_arch = st.columns([1, 1])

            with col_pca:
                st.subheader("2. K-Means 2D PCA Financial Space")
                pca_data = cluster_info.get("pca_2d", [])
                if pca_data:
                    df_pca = pd.DataFrame(pca_data)
                    st.scatter_chart(
                        df_pca,
                        x="x",
                        y="y",
                        color="archetype",
                        size=20,
                    )
                    st.caption("2D PCA projection of the 15-dimensional financial feature vectors.")

            with col_arch:
                st.subheader("3. Discovered Investment Archetypes")
                clusters_dict = cluster_info.get("clusters", {})
                for cid, cinfo in clusters_dict.items():
                    with st.container():
                        st.markdown(f'<div class="metric-card"><h4>Cluster {cid}: {cinfo["name"]}</h4>'
                                    f'<p><strong>Members:</strong> {", ".join(cinfo["companies"])}</p></div>',
                                    unsafe_allow_html=True)
        else:
            st.info("Click 'Quick Seed Sample Universe' at top to populate multi-company peer dataset.")
    except Exception as e:
        st.error(f"Cluster benchmarking error: {e}")


# ==============================================================================
# TAB 4: Hybrid Recommendation & Explainability Studio
# ==============================================================================
with tab4:
    st.header("Hybrid Investment Recommendation & Explainability Studio (spec §15–§25)")

    col_pref1, col_pref2, col_pref3 = st.columns(3)

    with col_pref1:
        st.subheader("Investor Profile & Context")
        style = st.selectbox("Investment Style", ["Growth", "Value", "Income", "Balanced"], index=0)
        risk = st.selectbox("Risk Tolerance", ["Low", "Medium", "High"], index=1)
        sector_filter = st.selectbox("Sector Preference", ["All", "Technology", "Healthcare", "Utilities", "Consumer Discretionary"])
        portfolio_holdings = st.multiselect(
            "Existing Portfolio (Diversification Engine)",
            ["AAPL", "NVDA", "TSLA", "PFE", "NEE", "TCS", "RELIANCE", "HDFCBANK"],
            default=["AAPL"],
            help="The engine evaluates covariance and correlation with your basket to penalize concentration and reward diversification."
        )
        macro_choice = st.selectbox(
            "Macroeconomic Market Regime",
            ["Neutral / Balanced", "Rising Rates & Inflation", "Late-Cycle / Recession", "Expansionary / Bull Market"],
            index=0,
            help="Dynamically tilts scoring weights toward factors that outperform in the selected economic environment."
        )

    # Map friendly macro string to internal code
    regime_map = {
        "Neutral / Balanced": "neutral",
        "Rising Rates & Inflation": "rising_rates_inflation",
        "Late-Cycle / Recession": "recession_late_cycle",
        "Expansionary / Bull Market": "expansion_bull",
    }
    selected_regime = regime_map.get(macro_choice, "neutral")

    with col_pref2:
        st.subheader("Hard Constraints (spec §16)")
        max_de = st.slider("Max Debt-to-Equity", min_value=0.2, max_value=4.0, value=2.0, step=0.1)
        min_roe = st.slider("Min Return on Equity (%)", min_value=0, max_value=35, value=5, step=1) / 100.0
        min_growth = st.slider("Min Revenue Growth (%)", min_value=-20, max_value=30, value=-5, step=1) / 100.0

    with col_pref3:
        st.subheader("Risk & ESG Filters")
        max_beta = st.slider("Max Beta (Market Sensitivity)", min_value=0.5, max_value=2.5, value=2.0, step=0.1)
        min_esg = st.slider("Min ESG Score", min_value=40, max_value=95, value=65, step=5)
        min_mcap = st.number_input("Min Market Cap ($M)", min_value=0, value=10000, step=5000)

    if st.button("🚀 Run Hybrid Recommendation Engine", type="primary", use_container_width=True):
        with st.spinner("Executing hard filters, vector similarity, K-Means clustering, and generating grounded explanations..."):
            try:
                params = {
                    "investment_style": style,
                    "risk_tolerance": risk,
                    "preferred_sector": sector_filter if sector_filter != "All" else None,
                    "maximum_debt_equity": max_de,
                    "minimum_roe": min_roe,
                    "minimum_growth": min_growth,
                    "maximum_beta": max_beta,
                    "minimum_esg_score": float(min_esg),
                    "minimum_market_cap": float(min_mcap),
                    "current_holdings": portfolio_holdings,
                    "macro_regime": selected_regime,
                }
                resp = requests.post(f"{API_URL}/recommend/universe", params=params, timeout=30)
                if resp.ok:
                    rec_data = resp.json()
                    st.session_state.recommendations = rec_data
                else:
                    st.error(f"Recommendation failed: {resp.text}")
            except Exception as e:
                st.error(f"Error calling recommendation engine: {e}")

    # Display Ranked Recommendations
    if "recommendations" in st.session_state:
        recs = st.session_state.recommendations
        ranked = recs.get("ranked_recommendations", [])
        ineligible = recs.get("ineligible_companies", [])

        st.subheader(f"Ranked Investment Opportunities ({len(ranked)} Eligible / {recs.get('total_universe_size', 0)} Universe)")

        for item in ranked:
            exp = item["explanation"]
            meta = item.get("metadata", {})
            profile = exp.get("financial_profile", {})
            div_info = item.get("diversification_info") or exp.get("diversification") or {}
            qual_info = item.get("qualitative_info") or exp.get("qualitative_nlp") or {}

            with st.container():
                st.markdown(f"""
                <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="font-size: 1.4rem; font-weight: 700; color: #0F172A;">RANK #{item['rank']} — {item['company']} ({meta.get('ticker', '')})</span>
                            <span class="archetype-badge" style="margin-left: 15px;">{item['cluster_archetype']}</span>
                        </div>
                        <div style="text-align: right;">
                            <span style="font-size: 1.8rem; font-weight: 800; color: #2563EB;">{item['investment_match_score']}/100</span>
                            <div style="font-size: 0.8rem; color: #64748B;">Profile Match: {item['user_similarity_match']}%</div>
                        </div>
                    </div>
                    <div style="margin-top: 10px; display: flex; gap: 8px; flex-wrap: wrap;">
                        <span style="background-color: #F1F5F9; color: #334155; padding: 3px 8px; border-radius: 6px; font-size: 0.8rem; font-weight: 600;">📊 Content Score: {item.get('content_score', 'N/A')}</span>
                        <span style="background-color: #EFF6FF; color: #1E40AF; padding: 3px 8px; border-radius: 6px; font-size: 0.8rem; font-weight: 600;">🏛️ Inst. Co-Holding CF: {item.get('cf_score', 'N/A')}%</span>
                        <span style="background-color: #ECFDF5; color: #065F46; padding: 3px 8px; border-radius: 6px; font-size: 0.8rem; font-weight: 600;">🛡️ Diversification Score: {item.get('diversification_score', 'N/A')}/100 (Corr: {div_info.get('avg_correlation', 'N/A')})</span>
                        <span style="background-color: #FAF5FF; color: #6B21A8; padding: 3px 8px; border-radius: 6px; font-size: 0.8rem; font-weight: 600;">📝 10-K NLP Tone: {qual_info.get('sentiment_label', 'Neutral')} ({item.get('qualitative_score', 'N/A')}/100)</span>
                    </div>
                    <div style="margin-top: 10px; font-size: 0.9rem; color: #334155;">
                        <strong>Financial Profile:</strong> Growth: <em>{profile.get('Growth', 'N/A')}</em> | Profitability: <em>{profile.get('Profitability', 'N/A')}</em> | Health: <em>{profile.get('Financial Health', 'N/A')}</em> | Valuation: <em>{profile.get('Valuation', 'N/A')}</em> | Risk: <em>{profile.get('Risk', 'N/A')}</em> | ESG: <em>{profile.get('ESG', 'N/A')}</em>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col_str, col_risk = st.columns(2)
                with col_str:
                    st.markdown("**✓ Why Recommended (Strengths):**")
                    for s in exp.get("strengths", []):
                        st.markdown(f'<div class="strength-box">✓ {s}</div>', unsafe_allow_html=True)

                with col_risk:
                    st.markdown("**⚠ Key Risk Signals:**")
                    for r in exp.get("risks", []):
                        st.markdown(f'<div class="risk-box">⚠ {r}</div>', unsafe_allow_html=True)

                # Grounded 10-K Text Excerpts
                excerpts = qual_info.get("key_excerpts", [])
                if excerpts:
                    with st.expander(f"📖 Grounded 10-K Textual Excerpts & Disclosures ({len(excerpts)} cited passages)"):
                        for ex in excerpts:
                            badge = "🟢 Positive Disclosure" if ex.get("type") == "positive" else "🔴 Risk/Headwind"
                            st.markdown(f"""
                            <div style="border-left: 3px solid {'#10B981' if ex.get('type') == 'positive' else '#EF4444'}; padding: 6px 12px; margin-bottom: 8px; background-color: #F8FAFC;">
                                <small style="color: #64748B; font-weight: 600;">{badge} • Source: Page {ex.get('page', 2)}</small><br/>
                                <span style="font-size: 0.88rem; color: #1E293B; font-style: italic;">"{ex.get('text')}"</span>
                            </div>
                            """, unsafe_allow_html=True)

                # Traceability Citations
                citations = exp.get("traceability_citations", [])
                if citations:
                    with st.expander(f"🔍 View Source Document Citations ({len(citations)} metrics traced)"):
                        st.dataframe(pd.DataFrame(citations)[["metric", "value", "year", "source_page", "extraction_method", "confidence"]])

                st.caption(exp.get("grounding_statement", ""))
                st.write("")

        if ineligible:
            with st.expander(f"🚫 Ineligible Companies ({len(ineligible)} excluded by Hard Filters)"):
                for inel in ineligible:
                    st.write(f"**{inel['company']}** ({inel.get('metadata', {}).get('ticker', '')}):")
                    for reason in inel.get("failed_reasons", []):
                        st.write(f"  • {reason}")

# ==============================================================================
# TAB 5: Institutional Equity Research Report & Aesthetic DCF Studio
# ==============================================================================
with tab5:
    st.header("Institutional Equity Research & Aesthetic DCF Studio")
    st.markdown("Automated multi-stage valuation pipeline: **Document Extraction** ➔ **Accounting Identity Audits** ➔ **DuPont & Piotroski** ➔ **Interactive Aesthetic DCF Studio (zi-cong-tan design system)** ➔ **Institutional PDF Report**.")

    col_rep_in, col_rep_btn = st.columns([2, 1])
    with col_rep_in:
        selected_doc_id = st.number_input("Document ID to analyze", min_value=1, value=1, step=1, key="rep_doc_id")
        comp_ticker = st.text_input("Ticker Symbol", value="INFY")
        comp_name_in = st.text_input("Company Name", value="Infosys Limited")
        curr_price_in = st.number_input("Current Market Price (₹) [Live NSE: ₹1,023.40]", min_value=1.0, value=1023.40, step=10.0)

    with col_rep_btn:
        st.write("")
        st.write("")
        run_full_btn = st.button("⚡ Run End-to-End Pipeline & Generate Report", type="primary", use_container_width=True)

    if run_full_btn:
        with st.spinner("Executing full institutional analysis (Vision ➔ Audits ➔ DCF ➔ Peers ➔ PDF Report)..."):
            try:
                res = requests.post(f"{API_URL}/pipeline/full/{selected_doc_id}?company_name={comp_name_in}&ticker={comp_ticker}&current_price={curr_price_in}", timeout=120)
                if res.ok:
                    pipeline_result = res.json()
                    st.session_state.pipeline_result = pipeline_result
                    st.success("Successfully compiled Institutional Equity Research Report!")
                else:
                    st.error(f"Pipeline error: {res.text}")
            except Exception as e:
                st.error(f"Connection failure: {e}")

    if "pipeline_result" in st.session_state:
        p_res = st.session_state.pipeline_result
        dcf_sum = p_res.get("dcf_summary", {})
        val_sum = p_res.get("validation", {})
        dq_score = p_res.get("data_quality_score", 85.0)

        st.divider()
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric("Data Quality Score", f"{dq_score:.1f} / 100", help="Empirical accounting identity tie-outs (Assets = Liab + Equity, FCF, Net Income)")
        with col_m2:
            st.metric("Report DCF Baseline", f"₹{dcf_sum.get('intrinsic_value_per_share', 0):,.2f}")
        with col_m3:
            st.metric("Market Stock Price", f"₹{dcf_sum.get('current_price', 0):,.2f}")
        with col_m4:
            upside = dcf_sum.get("upside_pct", 0)
            st.metric("Baseline Upside", f"{'+' if upside >= 0 else ''}{upside:.1f}%")

        col_ev, col_val = st.columns([1, 1])
        with col_ev:
            st.markdown(f"""
            - **Enterprise Value:** ₹{dcf_sum.get('enterprise_value', 0):,.0f} Cr
            - **Discount Rate (WACC):** {dcf_sum.get('wacc', 0.118)*100:.2f}%
            - **Citations Extracted:** {p_res.get('citations_count', 0)} line items with bounding boxes
            - **Peers Benchmarked:** {p_res.get('peers_count', 0)} companies
            """)
        with col_val:
            st.markdown("**Accounting Audit Verification:**")
            failures = val_sum.get("failures", [])
            if not failures:
                st.success("✓ All accounting identity tests passed (Balance Sheet, Net Income, Cash Flow).")
            else:
                for f in failures:
                    st.warning(f"⚠ {f}")

        pdf_download_url = f"{API_URL}/report/{p_res['document_id']}?ticker={p_res.get('ticker', 'INFY')}"
        st.markdown(f'<a href="{pdf_download_url}" target="_blank"><button style="background-color: #2563EB; color: white; padding: 10px 24px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">📥 Download Official Research Report (PDF)</button></a>', unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # Aesthetic DCF Interactive Studio (zi-cong-tan/DCF-Calculator-Aesthetic)
    # --------------------------------------------------------------------------
    st.divider()
    st.subheader("🎨 Aesthetic DCF Interactive Studio")
    st.caption("Inspired by **zi-cong-tan/DCF-Calculator-Aesthetic**. The answer is at the top. Locked reported accounting figures are protected, and only forward-looking judgment calls are editable.")

    # Two column layout: Left = Assumptions Controls, Right = Live Aesthetic Output
    col_assump, col_display = st.columns([1, 2])

    with col_assump:
        st.markdown("### ⚙️ Your Assumptions")
        st.caption("Change the judgment calls. Reported figures and market prices are locked.")

        # Scenario Toggles
        col_scen1, col_scen2 = st.columns(2)
        with col_scen1:
            bear_toggle = st.toggle("🐻 Bear Case", value=st.session_state.get("dcf_bear_toggle", False), key="dcf_bear_toggle")
        with col_scen2:
            if st.button("🔄 Reset to Base", use_container_width=True):
                st.session_state.dcf_custom_lr = 23.0
                st.session_state.dcf_custom_tg = 4.5
                st.session_state.dcf_custom_roic = 22.0
                st.session_state.dcf_custom_beta = 0.85
                st.session_state.dcf_custom_kd = 7.6
                st.session_state.dcf_custom_tax = 25.0
                st.session_state.dcf_custom_inv = 3.5
                st.rerun()

        with st.expander("📊 Cost of Capital & Discount Rate", expanded=True):
            in_beta = st.slider("Beta (Market Sensitivity)", min_value=0.5, max_value=2.0, value=float(st.session_state.get("dcf_custom_beta", 0.85)), step=0.05, key="dcf_custom_beta")
            in_erp = st.slider("Equity Risk Premium (%)", min_value=3.5, max_value=8.0, value=5.5, step=0.1) / 100.0
            in_rf = st.slider("Risk-Free Rate (%) [10-Yr G-Sec]", min_value=5.0, max_value=9.0, value=7.1, step=0.1) / 100.0
            in_kd = st.slider("Cost of Debt before tax (%)", min_value=5.0, max_value=12.0, value=float(st.session_state.get("dcf_custom_kd", 7.6)), step=0.1, key="dcf_custom_kd") / 100.0

        with st.expander("📈 10-Year Revenue Growth Trajectory", expanded=False):
            st.caption("Enter expected annual top-line growth rates (%):")
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                g_y1 = st.number_input("2026E Growth (%)", value=8.0, step=0.5) / 100.0
                g_y2 = st.number_input("2027E Growth (%)", value=8.0, step=0.5) / 100.0
                g_y3 = st.number_input("2028E Growth (%)", value=7.0, step=0.5) / 100.0
                g_y4 = st.number_input("2029E Growth (%)", value=7.0, step=0.5) / 100.0
                g_y5 = st.number_input("2030E Growth (%)", value=6.0, step=0.5) / 100.0
            with col_g2:
                g_y6 = st.number_input("2031E Growth (%)", value=6.0, step=0.5) / 100.0
                g_y7 = st.number_input("2032E Growth (%)", value=5.5, step=0.5) / 100.0
                g_y8 = st.number_input("2033E Growth (%)", value=5.0, step=0.5) / 100.0
                g_y9 = st.number_input("2034E Growth (%)", value=4.5, step=0.5) / 100.0
                g_y10 = st.number_input("2035E Growth (%)", value=4.5, step=0.5) / 100.0
            growth_list = [g_y1, g_y2, g_y3, g_y4, g_y5, g_y6, g_y7, g_y8, g_y9, g_y10]

        with st.expander("🎯 Long-Run & Terminal Assumptions", expanded=True):
            in_lr = st.slider("Long-Run Operating Margin (%)", min_value=10.0, max_value=40.0, value=float(st.session_state.get("dcf_custom_lr", 23.0)), step=0.5, key="dcf_custom_lr", help="Moving this shifts terminal value and 2030-2035 margins") / 100.0
            in_tg = st.slider("Terminal Growth Rate (%)", min_value=1.5, max_value=6.0, value=float(st.session_state.get("dcf_custom_tg", 4.5)), step=0.25, key="dcf_custom_tg") / 100.0
            in_roic = st.slider("Terminal ROIC (%)", min_value=8.0, max_value=40.0, value=float(st.session_state.get("dcf_custom_roic", 22.0)), step=1.0, key="dcf_custom_roic", help="Reinvestment in terminal value = Growth ÷ ROIC") / 100.0
            in_tax = st.slider("Effective Tax Rate (%)", min_value=15.0, max_value=35.0, value=float(st.session_state.get("dcf_custom_tax", 25.0)), step=1.0, key="dcf_custom_tax") / 100.0
            in_inv = st.slider("Net Investment (% of Revenue)", min_value=1.0, max_value=15.0, value=float(st.session_state.get("dcf_custom_inv", 3.5)), step=0.5, key="dcf_custom_inv") / 100.0

    with col_display:
        # Call Backend Aesthetic DCF Endpoint
        try:
            params = {
                "company_name": comp_name_in,
                "ticker": comp_ticker,
                "current_price": curr_price_in,
                "beta": in_beta,
                "erp": in_erp,
                "rf": in_rf,
                "kd": in_kd,
                "tax_rate": in_tax,
                "terminal_growth": in_tg,
                "terminal_roic": in_roic,
                "long_run_margin": in_lr,
                "net_investment_pct": in_inv,
                "bear_case": bear_toggle,
            }
            # Append growth list
            query_str = "&".join([f"custom_growth_rates={g}" for g in growth_list])
            aest_resp = requests.post(f"{API_URL}/dcf/aesthetic/{selected_doc_id}?{query_str}", params=params, timeout=20)
            
            if aest_resp.ok:
                a_data = aest_resp.json()
                hero = a_data["hero"]
                facts_list = a_data["locked_facts"]
                bridge_list = a_data["equity_bridge"]
                forecast_rows = a_data["forecast_table"]
                sens = a_data["sensitivity"]

                val_ps = hero["value_per_share"]
                px = hero["current_price"]
                up_pct = hero["upside_pct"]
                imp_margin = hero["implied_long_run_margin_needed"]
                curr_lr = hero["current_long_run_margin"]
                is_above = hero["is_above_price"]

                # 1. Aesthetic Hero Stat Banner (The Answer First)
                st.markdown(f"""
                <div class="aesthetic-hero">
                    <div class="aesthetic-stat main">
                        <span class="lb">Intrinsic Value Per Share</span>
                        <span class="val">₹{val_ps:,.2f}</span>
                        <span class="sub-text">{"▲ Above" if is_above else "▼ Below"} price by <strong>{abs(up_pct):.1f}%</strong></span>
                    </div>
                    <div class="aesthetic-stat">
                        <span class="lb"><span class="lock-badge">LOCKED</span>Live Market Price</span>
                        <span class="val" style="color: #0F172A;">₹{px:,.2f}</span>
                        <span class="sub-text">NSE / BSE Quote</span>
                    </div>
                    <div class="aesthetic-stat">
                        <span class="lb">Margin Price Needs</span>
                        <span class="val" style="color: #2563EB;">{imp_margin:.1f}%</span>
                        <span class="sub-text">Yours: {curr_lr:.1f}% {"(Bear Case)" if bear_toggle else ""}</span>
                    </div>
                    <div class="aesthetic-stat">
                        <span class="lb">Discount Rate (WACC)</span>
                        <span class="val" style="color: #0F172A;">{hero['wacc']:.2f}%</span>
                        <span class="sub-text">Ke: {hero['cost_of_equity']:.1f}% | Debt: {hero['debt_weight']:.1f}%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if bear_toggle:
                    st.info("🐻 **Bear Case Active**: Long-run margin automatically throttled by -500 bps to model cyclical downside pressure.")

                # 2. Side-by-Side: Cash Flows to Share Price (Equity Bridge) vs Locked Facts
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    st.markdown("#### From Cash Flows to a Share Price")
                    st.caption(f"Valued in ₹ Crores • Mid-year discounting")
                    bridge_html = ""
                    for b in bridge_list:
                        row_cls = "waterfall-row total-row" if b.get("is_total") else "waterfall-row"
                        bridge_html += f"""
                        <div class="{row_cls}">
                            <span>{b['label']}</span>
                            <span>{b['value']}</span>
                        </div>
                        """
                    st.markdown(bridge_html, unsafe_allow_html=True)

                with col_b2:
                    st.markdown("#### 🔒 Locked Accounting Facts")
                    st.caption("Extracted from audited annual report filings (Protected from accidental tampering)")
                    facts_html = ""
                    for f in facts_list:
                        facts_html += f"""
                        <div class="waterfall-row">
                            <span><span class="lock-badge">FACT</span>{f['label']}</span>
                            <span style="font-weight: 600;">{f['value']}</span>
                        </div>
                        """
                    st.markdown(facts_html, unsafe_allow_html=True)

                # 3. 10-Year Forecast Table
                st.markdown("#### 📅 10-Year Full Valuation Projections (₹ Crores)")
                df_proj = pd.DataFrame(forecast_rows)
                df_proj = df_proj.rename(columns={
                    "year": "Fiscal Year",
                    "growth_pct": "Rev Growth (%)",
                    "revenue": "Revenue",
                    "margin_pct": "EBIT Margin (%)",
                    "ebit": "Operating Profit",
                    "nopat": "NOPAT (After Tax)",
                    "reinvestment": "Net Reinvestment",
                    "fcf": "Free Cash Flow",
                    "pv_fcf": "Present Value"
                })
                st.dataframe(df_proj.set_index("Fiscal Year"), use_container_width=True)

                # 4. 5x5 Sensitivity Matrix
                st.markdown("#### 🎯 Sensitivity Analysis: Intrinsic Value Per Share (₹)")
                st.caption("Rows: Discount Rate (WACC) • Columns: Long-Run Operating Margin • Center highlighted is your case, dashed is nearest market price.")
                
                wacc_hdrs = [f"{w:.2f}%" for w in sens["wacc_headers"]]
                margin_hdrs = [f"{m:.1f}%" for m in sens["margin_headers"]]
                df_sens = pd.DataFrame(sens["matrix"], index=wacc_hdrs, columns=margin_hdrs)
                
                # Render Clean HTML Grid with Highlighting
                nearest_r, nearest_c = sens.get("nearest_market_price_cell") or (2, 2)
                sens_table_html = "<table style='width:100%; text-align:center; border-collapse:collapse; font-size:0.92rem; border:1px solid #CBD5E1;'>"
                sens_table_html += "<tr style='background-color:#F1F5F9;'><th style='padding:8px; border:1px solid #CBD5E1;'>WACC ↓ / Margin →</th>"
                for m_h in margin_hdrs:
                    sens_table_html += f"<th style='padding:8px; border:1px solid #CBD5E1;'>{m_h}</th>"
                sens_table_html += "</tr>"

                for r_i, r_val in enumerate(sens["matrix"]):
                    sens_table_html += f"<tr><td style='padding:8px; font-weight:700; background-color:#F8FAFC; border:1px solid #CBD5E1;'>{wacc_hdrs[r_i]}</td>"
                    for c_i, cell_v in enumerate(r_val):
                        is_center = (r_i == 2 and c_i == 2)
                        is_nearest = (r_i == nearest_r and c_i == nearest_c)
                        
                        cell_style = "padding:8px; border:1px solid #CBD5E1;"
                        if is_center:
                            cell_style += "background-color:#0F766E; color:#FFFFFF; font-weight:800; border-radius:4px;"
                        elif is_nearest:
                            cell_style += "outline:2px dashed #DC2626; outline-offset:-2px; font-weight:700; background-color:#FEF2F2;"

                        cell_display_txt = f"₹{cell_v:,.1f}" if cell_v else "—"
                        sens_table_html += f"<td style='{cell_style}'>{cell_display_txt}</td>"
                    sens_table_html += "</tr>"
                sens_table_html += "</table>"
                
                st.markdown(sens_table_html, unsafe_allow_html=True)
                st.caption(f"🟩 Dark Teal Cell (Center) = Current Active Valuation (₹{val_ps:,.2f}) | 🟥 Dashed Border = Closest matrix outcome to market price ₹{px:,.2f}")

            else:
                st.error(f"Failed to calculate Aesthetic DCF: {aest_resp.text}")
        except Exception as e:
            st.error(f"Error communicating with Aesthetic DCF engine: {e}")

st.divider()
st.caption("FinSight AI — Academic Final System. Grounded in corporate annual report disclosures with quantitative transparency.")
