# Project Plan and Milestones

## Current Status

- [x] FastAPI backend with `upload`, `status`, `result`, `dashboard`, and `health` endpoints
- [x] PostgreSQL-backed job persistence
- [x] React frontend wired to live backend data
- [x] One-command local startup with `make dev`
- [x] Backend offline detection and clearer upload errors in the frontend
- [x] Mockup-faithful dashboard, upload, and results UI
- [x] Deterministic parsing for text, HTML, and DOCX files
- [x] Native PDF text extraction with PyMuPDF (`pdf_extractor.py`)

## Completed Frontend and Backend Work

- [x] Restore the dashboard, upload, and results layouts
- [x] Poll backend job status from the frontend
- [x] Render live result metadata, score, entities, and issues
- [x] Show real recent activity from the database
- [x] Add backend health visibility in the UI
- [x] Improve upload failure messages
- [x] Standardize local startup and environment setup
- [x] Lock local database direction to PostgreSQL

---

## Version 1 — In Progress

### 1. PDF Text Extraction (native, no OCR)

- [x] Integrate PyMuPDF and build a per-page extractor
- [x] Return per-page text, blocks, bounding boxes, and a unified output schema
- [ ] Wire `pdf_extractor` into the main result pipeline (replace the PDF placeholder in `ocr.py`)
- [ ] Extract PDF metadata (title, author, creation date, page count, encrypted flag)
- [ ] Handle encrypted/password-protected PDFs gracefully
- [ ] Handle corrupted, zero-byte, and oversized PDFs without crashing the worker
- [ ] Detect pages with little or no native text and flag them for v2 OCR fallback
- [ ] Surface per-page text in the API response so the frontend can render page-by-page

### 2. Document Parsers

- [ ] Add XLSX parsing
- [ ] Normalize all parser output (text, DOCX, PDF, XLSX) to one shared schema
- [ ] Add parser routing by MIME type and extension
- [ ] Add validation for unsupported or corrupted files
- [ ] Add resource limits (timeout, max pages, max bytes) per parse job

### 3. Embeddings and Vector Store

- [x] Define document chunking rules (size, overlap, page-aware boundaries) — page-anchored recursive splitter, 512 target / 64 overlap, tiktoken (cl100k_base)
- [x] Add chunk metadata fields (page, source file, char offsets, chunk index)
- [ ] Choose the embeddings model/provider
- [ ] Choose the vector database
- [ ] Save chunks and embeddings after extraction
- [ ] Add retrieval query helpers for regulations and prior documents

### 4. Agents and Orchestration

- [ ] Define each agent's responsibility and input/output schema
- [ ] Build the ingestion-to-reasoning flow
- [ ] Add LangGraph orchestration
- [ ] Add retry/fallback logic between agent steps
- [ ] Add traceable step logs for each agent run

### 5. Compliance Logic

- [ ] Define the compliance rule format
- [ ] Add real compliance checks
- [ ] Add structured findings with severity and explanation
- [ ] Add framework-level scoring logic
- [ ] Add audit trail records for every applied rule

---

## Version 2 — Deferred

### OCR for Scanned Documents and Images

Deferred from v1. Native PDF extraction covers the majority of business documents; OCR is added once the rest of the pipeline is shippable. The pipeline already has a hook (`v1` PDF extractor flags low-text pages) that v2 will consume.

- [ ] Choose the OCR engine (Tesseract / PaddleOCR / cloud — AWS Textract or Google Document AI)
- [ ] Add image OCR for PNG / JPG / JPEG / TIFF uploads
- [ ] Add OCR fallback for scanned PDF pages
- [ ] Confidence-based routing (native → OCR → vision LLM for the messy 5%)
- [ ] Per-block confidence scores in API output and UI
- [ ] Page-level progress events during long OCR jobs
- [ ] Layout-aware extraction (tables, forms, multi-column reading order)

### Other Future Work

- [ ] Show OCR confidence and parser source in more detail
- [ ] Add job history filtering and search
- [ ] Add result drill-down pages
- [ ] Add retry button for failed jobs
- [ ] Add export formats beyond plain text
- [ ] Add API tests for the live OCR and agent flows

---

## Suggested Build Order

1. Wire native PDF extractor into the main result pipeline
2. Add PDF metadata + error handling for encrypted / corrupted files
3. Normalize all parser output into one shared schema
4. Add chunking and embeddings
5. Plug in vector retrieval
6. Build agent orchestration
7. Replace placeholder scoring/issues with real compliance logic
8. (v2) Add OCR for scanned content

## Notes

- Local development is PostgreSQL-first. Do not switch the app back to SQLite.
- Keep each step shippable and testable before moving to the next one.
- OCR is intentionally deferred — v1 ships without it.
