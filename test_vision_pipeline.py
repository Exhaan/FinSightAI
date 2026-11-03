"""
Unit and Integration Tests for Phase B: Computer Vision Pipeline.
Run with: pytest tests/test_vision_pipeline.py -v
"""
import os
import fitz
from PIL import Image

from vision.page_renderer import render_page_image, render_document_thumbnails
from vision.page_classifier import classify_page_type, classify_document_pages
from vision.table_layout import TableLayoutExtractor
from vision.ocr_engine import DocumentOCREngine
from vision.visual_overlay import draw_bounding_box_overlay

PDF_PATH = "data/raw_documents/INFOSYS_Financial_Statements_FY24.pdf"


def test_page_renderer_produces_image():
    img, (w, h) = render_page_image(PDF_PATH, page_number=1, dpi=150)
    assert isinstance(img, Image.Image)
    assert w > 500
    assert h > 500


def test_page_classifier_identifies_statements():
    doc = fitz.open(PDF_PATH)
    # Page 1 in this slice is Balance Sheet Assets
    txt_bs = doc[0].get_text("text")
    # Page 3 in this slice is P&L
    txt_pl = doc[2].get_text("text")
    # Page 10 is Cash Flows
    txt_cf = doc[9].get_text("text")
    doc.close()

    res_bs = classify_page_type(txt_bs, page_number=1, total_pages=12)
    assert res_bs["page_type"] in ["balance_sheet", "notes"]

    res_pl = classify_page_type(txt_pl, page_number=3, total_pages=12)
    assert res_pl["page_type"] == "income_statement"

    res_cf = classify_page_type(txt_cf, page_number=10, total_pages=12)
    assert res_cf["page_type"] == "cash_flow"


def test_table_layout_extractor_finds_financial_rows():
    ext = TableLayoutExtractor()
    res = ext.extract_statement_table(PDF_PATH, page_number=3)
    assert res["page_number"] == 3
    assert len(res["financial_rows"]) >= 10
    
    # Check that Revenue from operations row is present
    rev_row = next((r for r in res["financial_rows"] if "Revenue from operations" in r["label"]), None)
    assert rev_row is not None
    assert len(rev_row["numeric_values"]) >= 2
    # Ensure bounding box is a valid 4-tuple
    assert len(rev_row["bbox"]) == 4
    assert rev_row["bbox"][0] < rev_row["bbox"][2]


def test_ocr_engine_detects_vector_vs_scanned():
    ocr = DocumentOCREngine()
    doc = fitz.open(PDF_PATH)
    page = doc[0]
    # Digital PDF page should not be flagged as scanned
    assert not ocr.is_page_scanned(page, min_chars=20)
    doc.close()


def test_bounding_box_overlay_draws_annotations():
    img, _ = render_page_image(PDF_PATH, page_number=3, dpi=100)
    citations = [
        {"metric": "Revenue", "value": "178650", "bbox": (50, 160, 550, 180), "category": "income"},
        {"metric": "Profit", "value": "29474", "bbox": (50, 450, 550, 470), "category": "income"},
    ]
    annotated = draw_bounding_box_overlay(img, citations, pdf_page_size=(612, 792))
    assert isinstance(annotated, Image.Image)
    assert annotated.size == img.size
