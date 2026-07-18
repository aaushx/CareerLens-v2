import logging

import fitz
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


def extract_text_with_ocr(filepath: str) -> str:
    """Extracts text from a PDF file page-by-page rendering pixmaps and calling pytesseract OCR."""
    extracted_text = ""
    try:
        with fitz.open(filepath) as doc:
            for page in doc:
                try:
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                    text = pytesseract.image_to_string(img)
                    extracted_text += text + "\n"
                except Exception as e:
                    logger.error(f"OCR failed for a page in {filepath}: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Failed to open PDF document {filepath} for OCR: {e}", exc_info=True)

    return extracted_text
