"""
Vision Module — Visual Bounding Box Overlay Generator (spec §4A).

Draws color-coded bounding boxes and metric labels over rendered page images:
- Green: Financial statement revenue / income metrics
- Blue: Balance sheet assets / liabilities
- Orange: Cash flow metrics
- Purple: Audited citations & notes

Outputs both:
1. Annotated image (PIL.Image / PNG file) for UI inspection
2. Coordinate payload for interactive Streamlit/HTML overlays
"""
import os
import fitz
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Any, Tuple, Optional

COLOR_MAP = {
    "income": (34, 197, 94, 200),     # Emerald green
    "balance": (59, 130, 246, 200),    # Blue
    "cash_flow": (249, 115, 22, 200),  # Orange
    "default": (168, 85, 247, 200),   # Purple
}


def draw_bounding_box_overlay(
    image: Image.Image,
    citations: List[Dict[str, Any]],
    pdf_page_size: Tuple[float, float],
    output_path: Optional[str] = None
) -> Image.Image:
    """
    Overlays citations onto a rendered PIL Image.
    citations: list of dicts with:
      - 'metric': name of metric
      - 'value': numeric value
      - 'bbox': (x0, y0, x1, y1) in PDF points (72 DPI)
      - 'category': 'income' | 'balance' | 'cash_flow' | 'default'
    """
    img_copy = image.copy()
    draw = ImageDraw.Draw(img_copy, "RGBA")
    
    img_w, img_h = image.size
    pdf_w, pdf_h = pdf_page_size

    scale_x = img_w / pdf_w if pdf_w > 0 else 1.0
    scale_y = img_h / pdf_h if pdf_h > 0 else 1.0

    for cit in citations:
        bbox = cit.get("bbox")
        if not bbox or len(bbox) != 4:
            continue

        # Scale from PDF points to image pixels
        x0 = bbox[0] * scale_x
        y0 = bbox[1] * scale_y
        x1 = bbox[2] * scale_x
        y1 = bbox[3] * scale_y

        cat = cit.get("category", "default")
        color = COLOR_MAP.get(cat, COLOR_MAP["default"])

        # Draw semi-transparent box
        fill_color = (color[0], color[1], color[2], 40)
        border_color = (color[0], color[1], color[2], 230)

        draw.rectangle([x0, y0, x1, y1], fill=fill_color, outline=border_color, width=3)

        # Draw text label banner above the box
        label_text = f"{cit.get('metric', '')}: {cit.get('value', '')}"
        draw.rectangle([x0, max(0, y0 - 20), min(img_w, x0 + len(label_text) * 9), y0], fill=border_color)
        draw.text((x0 + 4, max(0, y0 - 18)), label_text, fill=(255, 255, 255, 255))

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        img_copy.save(output_path, "PNG")

    return img_copy


class VisualOverlayGenerator:
    """
    Class wrapper for visual bounding box annotation generation.
    """

    def overlay_on_image(
        self,
        image: Image.Image,
        citations: List[Dict[str, Any]],
        pdf_page_size: Tuple[float, float],
        output_path: Optional[str] = None
    ) -> Image.Image:
        return draw_bounding_box_overlay(image, citations, pdf_page_size, output_path)

