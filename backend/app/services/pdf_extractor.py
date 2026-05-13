from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import fitz

from app.config import OCR_RENDER_DPI
from app.services import tesseract_ocr


MAX_PAGES = 1000
LOW_TEXT_THRESHOLD = 100
OCR_RECOVERY_MIN_CHARS = 20


def build_pdf_output(
    full_text: str,
    pages: List[Dict[str, Any]],
    meta: Dict[str, Any],
    warnings: List[Dict[str, str]],
) -> Dict[str, Any]:
    return {
        "full_text": full_text,
        "pages": pages,
        "meta": meta,
        "warnings": warnings,
    }


def empty_pdf_output(meta_overrides: Dict[str, Any], warnings: List[Dict[str, str]]) -> Dict[str, Any]:
    base_meta = {
        "source": "native",
        "engine": "pymupdf",
        "page_count": 0,
        "title": None,
        "author": None,
        "created_at": None,
        "is_encrypted": False,
        "avg_confidence": 0.0,
    }
    base_meta.update(meta_overrides)
    return build_pdf_output("", [], base_meta, warnings)


def open_pdf_document(file_path: Path) -> fitz.Document:
    return fitz.open(str(file_path))


def extract_page_text(page: fitz.Page) -> str:
    raw_text = page.get_text("text")
    return raw_text.strip() if raw_text else ""


def extract_page_blocks(page: fitz.Page) -> List[Dict[str, Any]]:
    page_blocks: List[Dict[str, Any]] = []

    for block in page.get_text("blocks"):
        if block[6] != 0:
            continue

        text = str(block[4]).strip()
        if not text:
            continue

        page_blocks.append(
            {
                "text": text,
                "bbox": [block[0], block[1], block[2], block[3]],
                "confidence": 1.0,
            }
        )

    return page_blocks


def extract_pdf_page(page: fitz.Page, page_number: int) -> Dict[str, Any]:
    page_text = extract_page_text(page)
    page_blocks = extract_page_blocks(page)

    return {
        "page_number": page_number,
        "text": page_text,
        "blocks": page_blocks,
    }


def parse_pdf_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None

    cleaned = value.strip()
    if cleaned.startswith("D:"):
        cleaned = cleaned[2:]
    cleaned = cleaned.split("+")[0].split("-")[0].split("Z")[0]

    for length, fmt in ((14, "%Y%m%d%H%M%S"), (12, "%Y%m%d%H%M"), (8, "%Y%m%d"), (6, "%Y%m"), (4, "%Y")):
        if len(cleaned) >= length:
            try:
                return datetime.strptime(cleaned[:length], fmt).isoformat()
            except ValueError:
                continue
    return None


def extract_pdf_metadata(document: fitz.Document) -> Dict[str, Any]:
    raw = document.metadata or {}
    return {
        "title": (raw.get("title") or "").strip() or None,
        "author": (raw.get("author") or "").strip() or None,
        "created_at": parse_pdf_date(raw.get("creationDate")),
        "page_count": document.page_count,
        "is_encrypted": bool(document.is_encrypted),
    }


def extract_pdf_text(file_path: Path) -> Dict[str, Any]:
    warnings: List[Dict[str, str]] = []

    if not file_path.exists():
        warnings.append({"code": "PDF-MISSING", "message": "File not found at the expected path."})
        return empty_pdf_output({}, warnings)

    if file_path.stat().st_size == 0:
        warnings.append({"code": "PDF-EMPTY-FILE", "message": "File is zero bytes."})
        return empty_pdf_output({}, warnings)

    try:
        document = open_pdf_document(file_path)
    except Exception as exc:
        warnings.append(
            {"code": "PDF-CORRUPTED", "message": f"PyMuPDF could not open the file: {exc.__class__.__name__}."}
        )
        return empty_pdf_output({}, warnings)

    try:
        if document.is_encrypted:
            unlocked = document.authenticate("")
            if not unlocked:
                warnings.append(
                    {"code": "PDF-ENCRYPTED", "message": "PDF is password-protected and could not be opened."}
                )
                return empty_pdf_output({"is_encrypted": True, "page_count": document.page_count}, warnings)

        meta_fields = extract_pdf_metadata(document)

        if meta_fields["page_count"] == 0:
            warnings.append({"code": "PDF-NO-PAGES", "message": "PDF has zero pages."})
            return empty_pdf_output(meta_fields, warnings)

        pages_to_read = meta_fields["page_count"]
        if pages_to_read > MAX_PAGES:
            warnings.append(
                {
                    "code": "PDF-PAGE-LIMIT",
                    "message": f"PDF has {pages_to_read} pages; only the first {MAX_PAGES} were extracted.",
                }
            )
            pages_to_read = MAX_PAGES

        pages: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []
        low_text_pages: List[int] = []
        ocr_applied_pages: List[int] = []
        ocr_failed_pages: List[int] = []
        ocr_confidences: List[float] = []
        ocr_available = tesseract_ocr.is_available()

        for page_number in range(1, pages_to_read + 1):
            try:
                page = document.load_page(page_number - 1)
                page_data = extract_pdf_page(page, page_number)
            except Exception as exc:
                warnings.append(
                    {
                        "code": "PDF-PAGE-ERROR",
                        "message": f"Page {page_number} could not be parsed ({exc.__class__.__name__}); skipped.",
                    }
                )
                continue

            native_length = len(page_data["text"])
            if native_length < LOW_TEXT_THRESHOLD and ocr_available:
                try:
                    ocr_page = tesseract_ocr.extract_pdf_page(
                        page,
                        page_number,
                        dpi=OCR_RENDER_DPI,
                    )
                    if len(ocr_page["text"]) >= max(native_length + 20, OCR_RECOVERY_MIN_CHARS):
                        page_data["text"] = ocr_page["text"]
                        page_data["blocks"] = ocr_page["blocks"]
                        ocr_applied_pages.append(page_number)
                        if ocr_page["avg_confidence"] > 0:
                            ocr_confidences.append(ocr_page["avg_confidence"])
                except Exception:
                    ocr_failed_pages.append(page_number)

            pages.append(page_data)
            full_text_parts.append(page_data["text"])
            if len(page_data["text"]) < LOW_TEXT_THRESHOLD:
                low_text_pages.append(page_number)

        full_text = "\n".join(full_text_parts).strip()

        if ocr_applied_pages:
            warnings.append(
                {
                    "code": "PDF-OCR-FALLBACK",
                    "message": (
                        f"OCR fallback was applied to {len(ocr_applied_pages)} low-text page(s): "
                        f"{ocr_applied_pages[:10]}{'…' if len(ocr_applied_pages) > 10 else ''}."
                    ),
                }
            )

        if low_text_pages:
            warnings.append(
                {
                    "code": "PDF-LOW-TEXT",
                    "message": (
                        f"{len(low_text_pages)} page(s) still have very little extractable text after processing: "
                        f"{low_text_pages[:10]}{'…' if len(low_text_pages) > 10 else ''}."
                    ),
                }
            )

        if low_text_pages and not ocr_available:
            warnings.append(
                {
                    "code": "OCR-UNAVAILABLE",
                    "message": "Tesseract OCR is not available, so low-text PDF pages could not use OCR fallback.",
                }
            )

        if ocr_failed_pages:
            warnings.append(
                {
                    "code": "OCR-FAILED",
                    "message": (
                        f"OCR fallback failed on page(s) {ocr_failed_pages[:10]}"
                        f"{'…' if len(ocr_failed_pages) > 10 else ''}."
                    ),
                }
            )

        if not full_text:
            warnings.append(
                {
                    "code": "PDF-NO-TEXT",
                    "message": "No readable text was extracted from the PDF after native parsing and OCR fallback.",
                }
            )

        meta = {
            "source": "hybrid" if ocr_applied_pages else "native",
            "engine": "pymupdf+tesseract" if ocr_applied_pages else "pymupdf",
            "avg_confidence": (sum(ocr_confidences) / len(ocr_confidences)) if ocr_confidences else 1.0,
            **meta_fields,
        }

        meta["text_source"] = "pdf-ocr" if ocr_applied_pages else "pdf-native"

        return build_pdf_output(full_text, pages, meta, warnings)
    finally:
        document.close()


if __name__ == "__main__":
    import json
    import sys

    target = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        Path(__file__).resolve().parent.parent.parent.parent / "assets" / "testocr" / "1.pdf"
    )
    result = extract_pdf_text(target)
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
