"""
SQLAlchemy models — spec section 12 (Database Design).

Tables:
    Company           — company profile, ticker, sector, market cap, risk metrics
    Document          — uploaded PDF document record (full source traceability)
    ExtractedMetric   — raw extracted values with page, method, and confidence
    FinancialMetrics  — standardized financial statements & derived ratios per company-year
    EsgMetrics        — ESG performance per company-year
    UserPreference    — user investment profile & constraints
"""
from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, DateTime, Text
)
from sqlalchemy.orm import relationship
from datetime import datetime

from database.database import Base


class Company(Base):
    __tablename__ = "companies"

    company_id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String, nullable=False, unique=True)
    ticker = Column(String, nullable=True)
    sector = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    market_cap = Column(Float, nullable=True)     # In millions
    beta = Column(Float, nullable=True)
    volatility = Column(Float, nullable=True)

    documents = relationship("Document", back_populates="company", cascade="all, delete-orphan")
    financial_metrics = relationship("FinancialMetrics", back_populates="company", cascade="all, delete-orphan")
    esg_metrics = relationship("EsgMetrics", back_populates="company", cascade="all, delete-orphan")


class Document(Base):
    """A single uploaded PDF, kept for full traceability back to source."""
    __tablename__ = "documents"

    document_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.company_id"), nullable=True)
    filename = Column(String, nullable=False)
    stored_path = Column(String, nullable=False)
    num_pages = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="documents")
    extracted_metrics = relationship("ExtractedMetric", back_populates="document", cascade="all, delete-orphan")


class ExtractedMetric(Base):
    """
    Raw extracted metric with full source traceability — spec §10:
    metric, value, year, source_page, document, extraction_method, confidence.
    """
    __tablename__ = "extracted_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.document_id"), nullable=False)
    metric = Column(String, nullable=False)            # e.g. "Revenue"
    value = Column(Float, nullable=True)
    year = Column(Integer, nullable=True)
    source_page = Column(Integer, nullable=True)
    extraction_method = Column(String, nullable=True)   # "native_text" | "table" | "ocr"
    confidence = Column(Float, nullable=True)
    raw_context = Column(Text, nullable=True)           # snippet from document
    flagged = Column(String, nullable=True)              # validation warning
    unit_scale = Column(String, default="raw")          # "millions", "thousands", etc.

    document = relationship("Document", back_populates="extracted_metrics")


class FinancialMetrics(Base):
    """Standardized numeric fields per company-year — spec §12 & §13."""
    __tablename__ = "financial_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.company_id"), nullable=False)
    year = Column(Integer, nullable=False)

    # Income Statement
    revenue = Column(Float, nullable=True)
    cost_of_revenue = Column(Float, nullable=True)
    gross_profit = Column(Float, nullable=True)
    operating_expenses = Column(Float, nullable=True)
    operating_income = Column(Float, nullable=True)
    ebit = Column(Float, nullable=True)
    ebitda = Column(Float, nullable=True)
    net_income = Column(Float, nullable=True)
    eps = Column(Float, nullable=True)

    # Balance Sheet
    cash = Column(Float, nullable=True)
    current_assets = Column(Float, nullable=True)
    assets = Column(Float, nullable=True)
    current_liabilities = Column(Float, nullable=True)
    debt = Column(Float, nullable=True)
    short_term_debt = Column(Float, nullable=True)
    long_term_debt = Column(Float, nullable=True)
    liabilities = Column(Float, nullable=True)
    equity = Column(Float, nullable=True)

    # Cash Flow Statement
    operating_cash_flow = Column(Float, nullable=True)
    capex = Column(Float, nullable=True)
    free_cash_flow = Column(Float, nullable=True)
    investing_cash_flow = Column(Float, nullable=True)
    financing_cash_flow = Column(Float, nullable=True)

    # Derived Ratios (Phase 3 & 4)
    revenue_growth = Column(Float, nullable=True)
    revenue_cagr = Column(Float, nullable=True)
    gross_margin = Column(Float, nullable=True)
    operating_margin = Column(Float, nullable=True)
    net_margin = Column(Float, nullable=True)
    roe = Column(Float, nullable=True)
    roic = Column(Float, nullable=True)
    debt_to_equity = Column(Float, nullable=True)
    debt_to_assets = Column(Float, nullable=True)
    current_ratio = Column(Float, nullable=True)
    interest_coverage = Column(Float, nullable=True)
    fcf_growth = Column(Float, nullable=True)
    pe_ratio = Column(Float, nullable=True)
    ev_ebitda = Column(Float, nullable=True)
    dcf_upside = Column(Float, nullable=True)

    company = relationship("Company", back_populates="financial_metrics")


class EsgMetrics(Base):
    """ESG performance metrics — spec §12."""
    __tablename__ = "esg_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.company_id"), nullable=False)
    year = Column(Integer, nullable=False)
    esg_score = Column(Float, nullable=True)
    environmental_score = Column(Float, nullable=True)
    social_score = Column(Float, nullable=True)
    governance_score = Column(Float, nullable=True)

    company = relationship("Company", back_populates="esg_metrics")


class UserPreference(Base):
    """User investment profile & risk filters — spec §12 & §24."""
    __tablename__ = "user_preferences"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    risk_tolerance = Column(String, default="Medium")       # Low / Medium / High
    investment_style = Column(String, default="Growth")     # Growth / Value / Income / Balanced
    investment_horizon = Column(String, default="Long-Term")# Short / Medium / Long-Term
    preferred_sector = Column(String, nullable=True)
    minimum_esg_score = Column(Float, nullable=True)
    maximum_beta = Column(Float, nullable=True)
    maximum_debt_equity = Column(Float, nullable=True)
    minimum_roe = Column(Float, nullable=True)
    minimum_growth = Column(Float, nullable=True)
