# Project Plan and Milestones

## Where we are

The product is a self-hosted compliance triage + document chat tool. It runs locally,
stores everything in a local Postgres + pgvector, and uses Hugging Face Inference for
embeddings and reasoning by default (with Anthropic Claude wired in as a swap-in).
Users own their rule set — defaults are seeded but fully editable.

---

## Version 1 — Shipped

### Foundations

- [x] FastAPI backend with `upload`, `status`, `result`, `dashboard`, `health` endpoints
- [x] PostgreSQL-backed job persistence with cascade-deletable chunks
- [x] React (Vite) frontend wired to live backend data
- [x] One-command local startup with `make dev`
- [x] Backend offline detection and clear upload errors in the UI
- [x] Pipeline trace logging for every upload + chat request (stdout)

### Document parsers

- [x] Native PDF text extraction with PyMuPDF, including:
  - [x] Per-page text + blocks + bounding boxes
  - [x] PDF metadata (title, author, creation date, page count, encryption flag)
  - [x] Graceful handling for encrypted, corrupted, zero-byte, and oversized PDFs
  - [x] Low-text page detection (flagged for future OCR fallback)
  - [x] Per-page output exposed via the API
- [x] DOCX parser (ZIP-based)
- [x] Plain text / HTML / source code parser with HTML tag stripping
- [x] XLSX parser via openpyxl (per-sheet, per-cell, with row/sheet caps)
- [x] Unified extraction schema across all parsers
- [x] Parser routing by extension + MIME type
- [x] File-level validation (existence, size cap, magic bytes for type)

### Embeddings + vector store

- [x] Page-anchored recursive chunking — `tiktoken` cl100k_base, 512 target / 64 overlap
- [x] Chunk metadata: page number, source filename, char offsets, chunk index, token count
- [x] Embeddings model — `BAAI/bge-small-en-v1.5` (384-dim) via Hugging Face Inference (free tier)
- [x] Vector store — pgvector extension on the existing Postgres instance
- [x] `/search` endpoint with cosine similarity, optional per-job scope
- [x] Per-job replace-and-reindex on every re-upload

### Compliance agent (LangGraph)

- [x] Pydantic types for `Finding`, `ComplianceReport`, `FrameworkSummary`
- [x] TypedDict `ComplianceState` shared across the graph
- [x] 3-node `StateGraph`: Retrieve → Reason → Score
- [x] Retrieve node loads rules from the database and supports any user-defined framework
- [x] Reason node calls a provider-agnostic LLM client with strict JSON output + parse retries
- [x] Score node aggregates findings into a 0–100 score with a 4-tier label
- [x] Graceful degradation if the LLM call fails (job still completes)
- [x] Pipeline trace lines: `AGENT.RETRIEVE`, `AGENT.REASON`, `AGENT.SCORE`, `AGENT.GRAPH-DONE`

### LLM provider abstraction

- [x] `app/agents/llm.py` — provider-agnostic chat completion
- [x] Hugging Face Inference (tested, default)
- [x] Anthropic Claude (implemented, untested — switchable via `LLM_PROVIDER`)
- [x] Lazy provider import — no install needed unless the provider is used

### User-editable compliance rules

- [x] `compliance_rules` table — `rule_id`, `framework`, `title`, `check`, `severity`, `is_default`, `is_enabled`
- [x] Defaults seeded on first boot only when the table is empty (15 rules across GDPR / SOC 2 / ISO 27001)
- [x] Full CRUD: `GET / POST / PUT / DELETE /rules`
- [x] `POST /rules/restore-defaults` — re-seeds missing defaults without touching customized rules
- [x] `GET /frameworks` — distinct framework labels for autocomplete and filter chips
- [x] Free-form framework names (HIPAA, PCI-DSS, "Internal Policy v3", etc. all work end-to-end)
- [x] Frontend Rules page — table, filter chips, stats, add/edit modal with framework autocomplete
- [x] Per-row enable toggle, edit, delete; "Restore Defaults" button

### Compliance UI

- [x] Compliance Score card (LLM-driven) — score, label, summary, framework chips with pass/warn/fail counts
- [x] Compliance Findings collapsible table — status badge, severity dot, rule code, framework chip, explanation, evidence
- [x] LLM provider/model line on the score card
- [x] Empty states when compliance is unavailable (legacy job, demo, LLM failure)
- [x] Framework toggles on the upload page driven by `/frameworks`
- [x] Export Report includes the compliance section

### Document chat

- [x] `POST /chat` — embeds question, runs cosine search, builds prompt with retrieved chunks + history, calls LLM
- [x] `GET /jobs` — list completed documents for the chat scope dropdown
- [x] Frontend Chat page — scope dropdown, user/assistant bubbles, typing indicator, citations expander, `Enter` to send
- [x] "Chat about this document" button on the Results page (jumps to a fresh, pre-scoped conversation)
- [x] Conversation persistence across navigation via `sessionStorage`
- [x] Citation chips show source filename, page, similarity score, and a 280-char preview

---

## Version 2 — Deferred

### OCR for scanned documents and images

The pipeline already flags low-text PDF pages so v2 just needs to add an OCR engine and route those pages to it.

- [ ] Choose engine — Tesseract, PaddleOCR, or a cloud provider (AWS Textract / Google Document AI)
- [ ] Image OCR for PNG / JPG / JPEG / TIFF uploads
- [ ] OCR fallback for scanned PDF pages
- [ ] Confidence-based routing — native → OCR → vision LLM for the messy 5%
- [ ] Per-block confidence scores in the API and the UI
- [ ] Page-level progress events during long OCR jobs
- [ ] Layout-aware extraction (tables, forms, multi-column reading order)

### Agent / observability enhancements

- [ ] Specialized retrieval agent and compliance agent splits (currently a single Reason node)
- [ ] MCP-style tool calling — `search_regulations`, `fetch_previous_cases`, `validate_rules`
- [ ] Reranking layer over the initial vector hits
- [ ] Langfuse observability — prompt versioning, token usage, latency, failure traces
- [ ] Real regulatory corpus indexed in pgvector — let the agent ground reasoning in actual GDPR / SOC 2 text
- [ ] Ambiguity surface — separate output channel for passages whose meaning is unclear or contradictory

### Product polish

- [ ] Job history filtering and search
- [ ] Result drill-down pages (per-finding, per-page evidence linking)
- [ ] Retry button for failed jobs
- [ ] Export formats beyond plain text (PDF report, JSON, CSV)
- [ ] Streamed chat responses
- [ ] Per-user / multi-tenant story (currently single-tenant by design)

### DevOps

- [ ] Dockerize the stack
- [ ] CI pipeline (lint + tests)
- [ ] One-shot deploy to AWS / GCP / Azure / Railway
- [ ] Integration test corpus of representative documents

---

## Notes

- Local development is PostgreSQL-first. Do not switch the app back to SQLite.
- Keep each step shippable and testable before moving to the next one.
- Every commit goes to `main` as a single author (`Ahmed Butt`) with no AI co-author lines.
- The framework name on a rule is purely a label. The actual compliance check lives in the rule's `check` field; the LLM uses its training knowledge plus that text. A real production version would index actual regulatory corpora — that is a v2 milestone.
