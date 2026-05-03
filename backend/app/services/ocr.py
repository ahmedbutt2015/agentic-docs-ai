import html
import mimetypes
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


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

MONTH_PATTERN = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
    r"Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)


def extract_document_data(
    file_path: Path,
    filename: Optional[str] = None,
    uploaded_at: Optional[datetime] = None,
    processed_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    text, text_source = _extract_text(file_path)
    entities = _extract_entities(text)
    metadata = _build_metadata(file_path, filename or file_path.name, text, text_source, uploaded_at, processed_at)
    issues = _build_issues(text, entities, metadata)
    score = _build_score(text, entities, issues, metadata)

    return {
        "text": text,
        "entities": entities,
        "metadata": metadata,
        "score": score,
        "issues": issues,
    }


def build_result_payload(
    file_path: Path,
    filename: str,
    uploaded_at: Optional[datetime],
    processed_at: Optional[datetime],
    text: Optional[str],
    entities: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    safe_text = text or ""
    safe_entities = entities or {}
    text_source = _infer_text_source(file_path, safe_text)
    metadata = _build_metadata(file_path, filename, safe_text, text_source, uploaded_at, processed_at)
    issues = _build_issues(safe_text, safe_entities, metadata)
    score = _build_score(safe_text, safe_entities, issues, metadata)

    return {
        "text": safe_text,
        "entities": safe_entities,
        "metadata": metadata,
        "score": score,
        "issues": issues,
    }


def _extract_text(file_path: Path) -> tuple[str, str]:
    extension = file_path.suffix.lower()

    if extension in TEXT_EXTENSIONS:
        return _clean_text(_read_text_file(file_path)), "text"

    if extension == ".docx":
        return _clean_text(_read_docx_text(file_path)), "docx"

    if extension == ".pdf":
        page_count = _count_pdf_pages(file_path)
        text = (
            "PDF uploaded successfully. Full text extraction is not enabled yet, "
            f"but {page_count or 'unknown'} page(s) were detected from the file structure."
        )
        return text, "pdf-placeholder"

    if extension in IMAGE_EXTENSIONS:
        return (
            "Image uploaded successfully. OCR is not enabled yet, so only file metadata is available for this document.",
            "image-placeholder",
        )

    return (
        f"{file_path.suffix.upper() or 'Unknown'} file uploaded successfully. "
        "Deep parsing for this file type is planned but not enabled yet.",
        "binary-placeholder",
    )


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
    text_source: str,
    uploaded_at: Optional[datetime],
    processed_at: Optional[datetime],
) -> Dict[str, Any]:
    stat_result = file_path.stat() if file_path.exists() else None
    file_size = stat_result.st_size if stat_result else 0
    mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    page_count = _count_pdf_pages(file_path) if file_path.suffix.lower() == ".pdf" else None

    return {
        "filename": filename,
        "extension": file_path.suffix.lower() or "unknown",
        "mime_type": mime_type,
        "file_size_bytes": file_size,
        "file_size_label": _format_file_size(file_size),
        "text_source": text_source,
        "uploaded_at": uploaded_at,
        "processed_at": processed_at,
        "character_count": len(text),
        "word_count": len(text.split()),
        "line_count": len([line for line in text.splitlines() if line.strip()]) or (1 if text else 0),
        "page_count": page_count,
    }


def _build_issues(text: str, entities: Dict[str, Any], metadata: Dict[str, Any]) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []

    if metadata["text_source"].endswith("placeholder"):
        issues.append(
            {
                "severity": "High",
                "severity_class": "sev-high",
                "rule": "EXTRACT-001",
                "description": "Full text extraction is not enabled for this file type yet, so the result only contains metadata and a placeholder summary.",
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

    if not any(key.startswith("date_") for key in entities):
        issues.append(
            {
                "severity": "Medium",
                "severity_class": "sev-medium",
                "rule": "ENTITY-101",
                "description": "No date-like values were detected in the current document output.",
            }
        )

    if not any(key.startswith("amount_") for key in entities):
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

    return issues


def _build_score(text: str, entities: Dict[str, Any], issues: List[Dict[str, str]], metadata: Dict[str, Any]) -> Dict[str, Any]:
    score = 100

    if metadata["text_source"].endswith("placeholder"):
        score -= 30
    if not text.strip():
        score -= 35
    if not entities:
        score -= 20
    if not any(key.startswith("date_") for key in entities):
        score -= 10
    if not any(key.startswith("amount_") for key in entities):
        score -= 5

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

    framework_status = [
        {"name": "Upload Metadata", "status": "complete"},
        {"name": "Text Extraction", "status": "complete" if text.strip() and not metadata["text_source"].endswith("placeholder") else "partial"},
        {"name": "Entity Detection", "status": "complete" if entities else "pending"},
        {"name": "Deferred OCR/AI", "status": "pending" if metadata["text_source"].endswith("placeholder") else "not_needed"},
    ]

    if issues and score > 90:
        score = 90

    return {
        "value": score,
        "label": label,
        "summary": summary,
        "frameworks": framework_status,
    }


def _count_pdf_pages(file_path: Path) -> Optional[int]:
    if not file_path.exists():
        return None

    try:
        content = file_path.read_bytes()
    except OSError:
        return None

    matches = re.findall(rb"/Type\s*/Page\b", content)
    return len(matches) or None


def _format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / 1024 / 1024:.1f} MB"


def _infer_text_source(file_path: Path, text: str) -> str:
    extension = file_path.suffix.lower()
    if extension in TEXT_EXTENSIONS:
        return "text"
    if extension == ".docx":
        return "docx"
    if extension == ".pdf":
        return "pdf-placeholder" if "not enabled yet" in text.lower() else "pdf"
    if extension in IMAGE_EXTENSIONS:
        return "image-placeholder"
    return "binary-placeholder"
