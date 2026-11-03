"""
Vision Module — High-Resolution Page Renderer (PyMuPDF).

Renders PDF document pages to 300 DPI images for:
1. High-accuracy Computer Vision & OCR layout processing.
2. Visual bounding box verification in the UI.
3. Multi-modal inspection of complex tables and scanned receipts.
"""
import os
import fitz  # PyMuPDF
from PIL import Image
import io
from typing import Optional, List, Tuple


def render_page_image(
    pdf_path: str,
    page_number: int,
    dpi: int = 300,
    output_path: Optional[str] = None
) -> Tuple[Image.Image, Tuple[int, int]]:
    """
    Renders a specific page (1-indexed) of a PDF to a high-res PIL Image.
    
    Args:
        pdf_path: Path to the PDF file
        page_number: 1-indexed page number
        dpi: Target DPI (standard 300 DPI for document vision)
        output_path: Optional path to save image file
        
    Returns:
        (PIL.Image, (width, height))
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    doc = fitz.open(pdf_path)
    if page_number < 1 or page_number > len(doc):
        doc.close()
        raise IndexError(f"Page {page_number} out of range [1, {len(doc)}]")

    page = doc[page_number - 1]
    zoom = dpi / 72.0  # 72 points per inch in PDF
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    size = (pix.width, pix.height)
    
    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        img.save(output_path, "PNG")

    doc.close()
    return img, size


def render_document_thumbnails(
    pdf_path: str,
    output_dir: str,
    max_pages: int = 20,
    dpi: int = 150
) -> List[str]:
    """
    Renders thumbnails for document browsing in the UI.
    """
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    saved_paths = []
    
    total = min(len(doc), max_pages)
    for i in range(total):
        page = doc[i]
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        out_file = os.path.join(output_dir, f"page_{i + 1}.png")
        pix.save(out_file)
        saved_paths.append(out_file)

    doc.close()
    return saved_paths
