from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

import fitz
from PIL import Image, ImageOps

from app.config import OCR_LANGUAGE, OCR_PSM, TESSERACT_CMD

try:
    import pytesseract
except ImportError:  # pragma: no cover - handled at runtime
    pytesseract = None


def _configure_tesseract() -> None:
    if pytesseract is not None and TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


@lru_cache(maxsize=1)
def is_available() -> bool:
    if pytesseract is None:
        return False

    _configure_tesseract()
    try:
        pytesseract.get_tesseract_version()
    except Exception:
        return False
    return True


def _preprocess_image(image: Image.Image) -> Image.Image:
    # Keep preprocessing light so we improve contrast without pulling in heavier CV deps.
    grayscale = ImageOps.grayscale(image)
    return ImageOps.autocontrast(grayscale)


def _coerce_confidence(raw_value: Any) -> Optional[float]:
    try:
        confidence = float(raw_value)
    except (TypeError, ValueError):
        return None
    if confidence < 0:
        return None
    return confidence / 100.0 if confidence > 1 else confidence


def _extract_blocks(image: Image.Image) -> Dict[str, Any]:
    if not is_available():
        raise RuntimeError("Tesseract OCR is not available.")

    processed_image = _preprocess_image(image)
    data = pytesseract.image_to_data(
        processed_image,
        lang=OCR_LANGUAGE,
        config=f"--psm {OCR_PSM}",
        output_type=pytesseract.Output.DICT,
    )

    blocks: List[Dict[str, Any]] = []
    line_groups: Dict[tuple, List[str]] = {}
    confidences: List[float] = []

    total_items = len(data.get("text", []))
    for index in range(total_items):
        text = str(data["text"][index] or "").strip()
        confidence = _coerce_confidence(data["conf"][index])
        if not text:
            continue

        block = {
            "text": text,
            "bbox": [
                float(data["left"][index]),
                float(data["top"][index]),
                float(data["left"][index] + data["width"][index]),
                float(data["top"][index] + data["height"][index]),
            ],
            "confidence": confidence if confidence is not None else 0.0,
        }
        blocks.append(block)
        line_key = (
            int(data["block_num"][index]),
            int(data["par_num"][index]),
            int(data["line_num"][index]),
        )
        line_groups.setdefault(line_key, []).append(text)
        if confidence is not None:
            confidences.append(confidence)

    text_lines = [" ".join(words).strip() for _, words in sorted(line_groups.items()) if words]

    return {
        "text": "\n".join(text_lines).strip(),
        "blocks": blocks,
        "avg_confidence": (sum(confidences) / len(confidences)) if confidences else 0.0,
    }


def extract_image_file(file_path: Path) -> Dict[str, Any]:
    with Image.open(file_path) as image:
        rgb_image = image.convert("RGB")
        result = _extract_blocks(rgb_image)

    return {
        "page_number": 1,
        "text": result["text"],
        "blocks": result["blocks"],
        "avg_confidence": result["avg_confidence"],
    }


def extract_pdf_page(page: Any, page_number: int, dpi: int = 200) -> Dict[str, Any]:
    zoom = dpi / 72.0
    pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    image = Image.open(BytesIO(pixmap.tobytes("png"))).convert("RGB")
    result = _extract_blocks(image)
    return {
        "page_number": page_number,
        "text": result["text"],
        "blocks": result["blocks"],
        "avg_confidence": result["avg_confidence"],
    }
