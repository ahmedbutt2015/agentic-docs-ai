import html
import mimetypes
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from app.services import pdf_extractor, xlsx_extractor
from app.services.processing_options import (
    build_processing_details_response,
    normalize_processing_options,
)
from app.services import tesseract_ocr


TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".html",
    ".htm",
    ".xml",
    ".yaml",
    ".yml",
    ".log",
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".css",
}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tif", ".tiff"}

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

MONTH_PATTERN = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
    r"Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)


def extract_document_data(
    file_path: Path,
    filename: Optional[str] = None,
    uploaded_at: Optional[datetime] = None,
    processed_at: Optional[datetime] = None,
    extraction: Optional[Dict[str, Any]] = None,
    processing_options: Optional[Dict[str, Any]] = None,
    processing_details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if extraction is None:
        extraction = run_extraction(file_path)
    text = extraction["full_text"]
    options = normalize_processing_options(processing_options)
    entities = _extract_entities(text) if options["extract_entities"] else {}
    metadata = _build_metadata(
        file_path, filename or file_path.name, text, extraction["meta"], uploaded_at, processed_at
    )
    issues = _build_issues(text, entities, metadata, extraction["warnings"], processing_options=options)
    score = _build_score(
        text,
        entities,
        issues,
        metadata,
        processing_options=options,
        processing_details=processing_details,
    )

    return {
        "text": text,
        "entities": entities,
        "metadata": metadata,
        "score": score,
        "issues": issues,
        "pages": extraction["pages"],
        "warnings": extraction["warnings"],
        "processing": build_processing_details_response(
            processing_details or {"options": options}
        ),
    }


def build_result_payload(
    file_path: Path,
    filename: str,
    uploaded_at: Optional[datetime],
    processed_at: Optional[datetime],
    text: Optional[str],
    entities: Optional[Dict[str, Any]],
    processing_options: Optional[Dict[str, Any]] = None,
    processing_details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    extraction = run_extraction(file_path)
    safe_text = text if text is not None else extraction["full_text"]
    options = normalize_processing_options(processing_options)
    safe_entities = entities or {}
    metadata = _build_metadata(file_path, filename, safe_text, extraction["meta"], uploaded_at, processed_at)
    issues = _build_issues(
        safe_text,
        safe_entities,
        metadata,
        extraction["warnings"],
        processing_options=options,
    )
    score = _build_score(
        safe_text,
        safe_entities,
        issues,
        metadata,
        processing_options=options,
        processing_details=processing_details,
    )

    return {
        "text": safe_text,
        "entities": safe_entities,
        "metadata": metadata,
        "score": score,
        "issues": issues,
        "pages": extraction["pages"],
        "warnings": extraction["warnings"],
        "processing": build_processing_details_response(
            processing_details or {"options": options}
        ),
    }


def run_extraction(file_path: Path) -> Dict[str, Any]:
    """Route a file to the right specialized extractor and return a unified shape."""
    extension = file_path.suffix.lower()
    pre_warnings = _validate_file(file_path)

    if any(w["code"] in {"FILE-MISSING", "FILE-OVERSIZED"} for w in pre_warnings):
        return _empty_extraction(
            text_source="error",
            engine="none",
            warnings=pre_warnings,
        )

    if extension == ".pdf":
        result = pdf_extractor.extract_pdf_text(file_path)
        result["meta"]["text_source"] = result["meta"].get("text_source") or "pdf-native"
        result["warnings"] = pre_warnings + result["warnings"]
        return result

    if extension == ".xlsx":
        result = xlsx_extractor.extract_xlsx_text(file_path)
        result["meta"]["text_source"] = "xlsx"
        result["warnings"] = pre_warnings + result["warnings"]
        return result

    if extension in TEXT_EXTENSIONS:
        text = _clean_text(_read_text_file(file_path))
        return _wrap_text_extraction(
            text=text,
            text_source="text",
            engine="plain",
            warnings=pre_warnings,
        )

    if extension == ".docx":
        text = _clean_text(_read_docx_text(file_path))
        warnings = list(pre_warnings)
        if "internal document XML could not be parsed" in text.lower():
            warnings.append(
                {"code": "DOCX-CORRUPTED", "message": "DOCX archive is missing or unreadable."}
            )
        return _wrap_text_extraction(
            text=text,
            text_source="docx",
            engine="docx-zip",
            warnings=warnings,
        )

    if extension in IMAGE_EXTENSIONS:
        return _extract_image_with_ocr(file_path, pre_warnings)

    placeholder = (
        f"{file_path.suffix.upper() or 'Unknown'} file uploaded successfully. "
        "Deep parsing for this file type is planned but not enabled yet."
    )
    return _wrap_text_extraction(
        text=placeholder,
        text_source="binary-placeholder",
        engine="placeholder",
        warnings=pre_warnings,
    )


def _validate_file(file_path: Path) -> List[Dict[str, str]]:
    warnings: List[Dict[str, str]] = []
    if not file_path.exists():
        warnings.append({"code": "FILE-MISSING", "message": "File not found at the expected path."})
        return warnings

    size = file_path.stat().st_size
    if size == 0:
        warnings.append({"code": "FILE-EMPTY", "message": "File is zero bytes."})
    if size > MAX_FILE_SIZE_BYTES:
        warnings.append(
            {
                "code": "FILE-OVERSIZED",
                "message": (
                    f"File is {size} bytes, exceeding the {MAX_FILE_SIZE_BYTES}-byte limit; "
                    "extraction was skipped."
                ),
            }
        )

    return warnings


def _extract_image_with_ocr(file_path: Path, warnings: List[Dict[str, str]]) -> Dict[str, Any]:
    if not tesseract_ocr.is_available():
        fallback_warnings = list(warnings)
        fallback_warnings.append(
            {
                "code": "OCR-UNAVAILABLE",
                "message": "Tesseract OCR is not available, so image text could not be extracted.",
            }
        )
        return _wrap_text_extraction(
            text="Image uploaded, but OCR is unavailable in the current backend environment.",
            text_source="image-placeholder",
            engine="placeholder",
            warnings=fallback_warnings,
        )

    try:
        page = tesseract_ocr.extract_image_file(file_path)
    except Exception as exc:
        fallback_warnings = list(warnings)
        fallback_warnings.append(
            {
                "code": "OCR-FAILED",
                "message": f"Image OCR failed with {exc.__class__.__name__}.",
            }
        )
        return _wrap_text_extraction(
            text="Image OCR failed, so only limited metadata is available for this document.",
            text_source="image-placeholder",
            engine="placeholder",
            warnings=fallback_warnings,
        )

    ocr_warnings = list(warnings)
    if not page["text"]:
        ocr_warnings.append(
            {
                "code": "OCR-NO-TEXT",
                "message": "Image OCR completed but did not detect readable text.",
            }
        )

    return {
        "full_text": page["text"],
        "pages": [
            {
                "page_number": 1,
                "text": page["text"],
                "blocks": page["blocks"],
            }
        ],
        "meta": {
            "source": "ocr",
            "engine": "tesseract",
            "page_count": 1,
            "title": None,
            "author": None,
            "created_at": None,
            "is_encrypted": False,
            "avg_confidence": page["avg_confidence"],
            "text_source": "image-ocr",
        },
        "warnings": ocr_warnings,
    }


def _empty_extraction(text_source: str, engine: str, warnings: List[Dict[str, str]]) -> Dict[str, Any]:
    return {
        "full_text": "",
        "pages": [],
        "meta": {
            "source": text_source,
            "engine": engine,
            "page_count": 0,
            "title": None,
            "author": None,
            "created_at": None,
            "is_encrypted": False,
            "avg_confidence": 0.0,
            "text_source": text_source,
        },
        "warnings": warnings,
    }


def _wrap_text_extraction(
    text: str,
    text_source: str,
    engine: str,
    warnings: List[Dict[str, str]],
) -> Dict[str, Any]:
    return {
        "full_text": text,
        "pages": [],
        "meta": {
            "source": text_source,
            "engine": engine,
            "page_count": None,
            "title": None,
            "author": None,
            "created_at": None,
            "is_encrypted": False,
            "avg_confidence": 1.0,
            "text_source": text_source,
        },
        "warnings": warnings,
    }


def _read_text_file(file_path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            raw_text = file_path.read_text(encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raw_text = file_path.read_text(encoding="utf-8", errors="ignore")

    if file_path.suffix.lower() in {".html", ".htm", ".xml"}:
        raw_text = re.sub(r"<\s*br\s*/?\s*>", "\n", raw_text, flags=re.IGNORECASE)
        raw_text = re.sub(r"</\s*(p|div|section|article|li|tr|h[1-6])\s*>", "\n", raw_text, flags=re.IGNORECASE)
        raw_text = re.sub(r"<[^>]+>", " ", raw_text)
        raw_text = html.unescape(raw_text)

    return raw_text


def _read_docx_text(file_path: Path) -> str:
    try:
        with zipfile.ZipFile(file_path) as archive:
            xml_text = archive.read("word/document.xml").decode("utf-8", errors="ignore")
    except (KeyError, zipfile.BadZipFile, FileNotFoundError):
        return "DOCX uploaded successfully, but the internal document XML could not be parsed."

    xml_text = xml_text.replace("</w:p>", "\n")
    xml_text = re.sub(r"<w:tab[^>]*/>", "\t", xml_text)
    xml_text = re.sub(r"<[^>]+>", " ", xml_text)
    return html.unescape(xml_text)


def _clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _extract_entities(text: str) -> Dict[str, Any]:
    if not text.strip():
        return {}

    patterns = {
        "amount": re.compile(r"(?:USD\s*)?\$\s?\d[\d,]*(?:\.\d{2})?(?:\s?[A-Z]{2,5})?", re.IGNORECASE),
        "date": re.compile(rf"\b{MONTH_PATTERN}\s+\d{{1,2}},\s+\d{{4}}\b|\b\d{{4}}-\d{{2}}-\d{{2}}\b"),
        "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
        "organization": re.compile(
            r"\b[A-Z][A-Za-z0-9&.,'-]*(?:\s+[A-Z][A-Za-z0-9&.,'-]*)*\s+"
            r"(?:Inc\.?|LLC|Ltd\.?|Corporation|Corp\.?|Company|Technologies|Tech|Bank|University)\b"
        ),
        "person": re.compile(r"\b(?:Mr\.|Mrs\.|Ms\.|Dr\.)?\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b"),
        "clause": re.compile(r"\b(?:Article|Section|Clause)\s+[A-Z0-9.\-]+\b|\b\d+\s+days['’]?\s+\w+\s+notice\b", re.IGNORECASE),
    }

    entities: Dict[str, Any] = {}
    for entity_type, pattern in patterns.items():
        values = _unique_matches(pattern.findall(text))
        for index, value in enumerate(values[:5], start=1):
            entities[f"{entity_type}_{index}"] = value.strip()

    return entities


def _unique_matches(matches: Iterable[Any]) -> List[str]:
    seen = set()
    results: List[str] = []

    for match in matches:
        value = " ".join(match).strip() if isinstance(match, tuple) else str(match).strip()
        normalized = re.sub(r"\s+", " ", value.lower())
        if not value or normalized in seen:
            continue
        seen.add(normalized)
        results.append(value)

    return results


def _build_metadata(
    file_path: Path,
    filename: str,
    text: str,
    parser_meta: Dict[str, Any],
    uploaded_at: Optional[datetime],
    processed_at: Optional[datetime],
) -> Dict[str, Any]:
    stat_result = file_path.stat() if file_path.exists() else None
    file_size = stat_result.st_size if stat_result else 0
    mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    text_source = parser_meta.get("text_source") or parser_meta.get("source") or "unknown"

    return {
        "filename": filename,
        "extension": file_path.suffix.lower() or "unknown",
        "mime_type": mime_type,
        "file_size_bytes": file_size,
        "file_size_label": _format_file_size(file_size),
        "text_source": text_source,
        "parser_engine": parser_meta.get("engine"),
        "uploaded_at": uploaded_at,
        "processed_at": processed_at,
        "character_count": len(text),
        "word_count": len(text.split()),
        "line_count": len([line for line in text.splitlines() if line.strip()]) or (1 if text else 0),
        "page_count": parser_meta.get("page_count"),
        "document_title": parser_meta.get("title"),
        "document_author": parser_meta.get("author"),
        "document_created_at": parser_meta.get("created_at"),
        "is_encrypted": bool(parser_meta.get("is_encrypted")),
    }


def _build_issues(
    text: str,
    entities: Dict[str, Any],
    metadata: Dict[str, Any],
    warnings: List[Dict[str, str]],
    processing_options: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, str]]:
    options = normalize_processing_options(processing_options)
    issues: List[Dict[str, str]] = []

    if metadata["text_source"].endswith("placeholder"):
        issues.append(
            {
                "severity": "High",
                "severity_class": "sev-high",
                "rule": "EXTRACT-001",
                "description": (
                    "Full text extraction is not enabled for this file type yet, so the result only "
                    "contains metadata and a placeholder summary."
                ),
            }
        )

    if not text.strip():
        issues.append(
            {
                "severity": "High",
                "severity_class": "sev-high",
                "rule": "TEXT-001",
                "description": "No readable text was extracted from the uploaded document.",
            }
        )

    if options["extract_entities"] and not any(key.startswith("date_") for key in entities):
        issues.append(
            {
                "severity": "Medium",
                "severity_class": "sev-medium",
                "rule": "ENTITY-101",
                "description": "No date-like values were detected in the current document output.",
            }
        )

    if options["extract_entities"] and not any(key.startswith("amount_") for key in entities):
        issues.append(
            {
                "severity": "Low",
                "severity_class": "sev-low",
                "rule": "ENTITY-102",
                "description": "No currency amount was detected in the current document output.",
            }
        )

    if metadata["file_size_bytes"] > 10 * 1024 * 1024:
        issues.append(
            {
                "severity": "Low",
                "severity_class": "sev-low",
                "rule": "FILE-201",
                "description": "This file is larger than 10 MB and may benefit from chunked parsing later.",
            }
        )

    for warning in warnings:
        issues.append(
            {
                "severity": _warning_severity(warning["code"]),
                "severity_class": _warning_severity_class(warning["code"]),
                "rule": warning["code"],
                "description": warning["message"],
            }
        )

    return issues


def _warning_severity(code: str) -> str:
    if code in {"FILE-MISSING", "FILE-OVERSIZED", "PDF-CORRUPTED", "PDF-ENCRYPTED",
                "XLSX-CORRUPTED", "XLSX-ENCRYPTED", "DOCX-CORRUPTED", "PDF-NO-TEXT",
                "OCR-FAILED", "OCR-UNAVAILABLE"}:
        return "High"
    if code in {"PDF-LOW-TEXT", "PDF-PAGE-LIMIT", "XLSX-SHEET-LIMIT", "XLSX-ROW-LIMIT",
                "PDF-PAGE-ERROR", "XLSX-SHEET-ERROR", "PDF-OCR-FALLBACK", "OCR-NO-TEXT"}:
        return "Medium"
    return "Low"


def _warning_severity_class(code: str) -> str:
    return {
        "High": "sev-high",
        "Medium": "sev-medium",
        "Low": "sev-low",
    }[_warning_severity(code)]


def _build_score(
    text: str,
    entities: Dict[str, Any],
    issues: List[Dict[str, str]],
    metadata: Dict[str, Any],
    processing_options: Optional[Dict[str, Any]] = None,
    processing_details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    options = normalize_processing_options(processing_options)
    details = processing_details if isinstance(processing_details, dict) else {}
    score = 100

    if metadata["text_source"].endswith("placeholder"):
        score -= 30
    if not text.strip():
        score -= 35
    if options["extract_entities"] and not entities:
        score -= 20
    if options["extract_entities"] and not any(key.startswith("date_") for key in entities):
        score -= 10
    if options["extract_entities"] and not any(key.startswith("amount_") for key in entities):
        score -= 5
    if metadata.get("is_encrypted"):
        score -= 25

    score = max(score, 10)

    if score >= 85:
        label = "Ready"
        summary = "The current backend extracted usable text and metadata for this document."
    elif score >= 60:
        label = "Partial"
        summary = "The backend captured some useful document data, but richer extraction is still pending."
    else:
        label = "Needs Enrichment"
        summary = "Only limited document data is available right now, so downstream analysis should wait."

    if not options["extract_entities"]:
        summary += " Entity extraction was skipped by configuration."
    if not options["index_for_chat"]:
        summary += " Chat indexing was skipped by configuration."
    if not options["run_compliance_check"]:
        summary += " Compliance scoring was skipped by configuration."

    extraction_status = (
        "complete"
        if text.strip() and not metadata["text_source"].endswith("placeholder")
        else "partial"
    )
    entity_status = "skipped" if not options["extract_entities"] else ("complete" if entities else "pending")

    chunks_indexed = int(details.get("chunks_indexed") or 0)
    if not options["index_for_chat"]:
        indexing_status = "skipped"
    elif details.get("indexing_status") == "failed":
        indexing_status = "failed"
    elif chunks_indexed > 0:
        indexing_status = "complete"
    else:
        indexing_status = "pending"

    compliance_status = str(details.get("compliance_status") or "").strip().lower()
    if not options["run_compliance_check"]:
        compliance_stage_status = "skipped"
    elif compliance_status in {"complete", "failed"}:
        compliance_stage_status = compliance_status
    else:
        compliance_stage_status = "pending"

    framework_status = [
        {"name": "Text Extraction", "status": extraction_status},
        {"name": "Entity Extraction", "status": entity_status},
        {"name": "Chat Indexing", "status": indexing_status},
        {"name": "Compliance Scoring", "status": compliance_stage_status},
    ]

    if issues and score > 90:
        score = 90

    return {
        "value": score,
        "label": label,
        "summary": summary,
        "frameworks": framework_status,
    }


def _format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / 1024 / 1024:.1f} MB"
