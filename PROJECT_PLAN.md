# Project Plan and Milestones

## Current Status

- [x] FastAPI backend with `upload`, `status`, `result`, `dashboard`, and `health` endpoints
- [x] PostgreSQL-backed job persistence
- [x] React frontend wired to live backend data
- [x] One-command local startup with `make dev`
- [x] Backend offline detection and clearer upload errors in the frontend
- [x] Mockup-faithful dashboard, upload, and results UI
- [x] Deterministic parsing for text, HTML, and DOCX files

## Completed Frontend and Backend Work

- [x] Restore the dashboard, upload, and results layouts
- [x] Poll backend job status from the frontend
- [x] Render live result metadata, score, entities, and issues
- [x] Show real recent activity from the database
- [x] Add backend health visibility in the UI
- [x] Improve upload failure messages
- [x] Standardize local startup and environment setup
- [x] Lock local database direction to PostgreSQL

## Next Steps You Can Build

### 1. OCR Implementation

- [ ] Choose the first OCR engine
- [ ] Add PDF text extraction
- [ ] Add image OCR for PNG/JPG/JPEG/TIFF
- [ ] Store extracted full text in `document_jobs`
- [ ] Return OCR confidence data in the API
- [ ] Add page-level progress updates during OCR

### 2. Document Parsers

- [ ] Add XLSX parsing
- [ ] Add richer PDF metadata extraction
- [ ] Normalize parser output to one shared schema
- [ ] Add parser routing by MIME type and extension
- [ ] Add validation for unsupported or corrupted files

### 3. Embeddings and Vector Store

- [ ] Define document chunking rules
- [ ] Choose the embeddings model/provider
- [ ] Choose the vector database
- [ ] Add chunk metadata fields
- [ ] Save chunks and embeddings after extraction
- [ ] Add retrieval query helpers for regulations and prior documents

### 4. Agents and Orchestration

- [ ] Define each agent’s responsibility and input/output schema
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

## Suggested Build Order

- [ ] Start with real PDF and image OCR
- [ ] Then normalize extraction output into one shared schema
- [ ] Then add chunking and embeddings
- [ ] Then plug in vector retrieval
- [ ] Then build agent orchestration
- [ ] Then replace the placeholder scoring/issues with real compliance logic

## Frontend and Backend Follow-Up After OCR/Agents

- [ ] Show OCR confidence and parser source in more detail
- [ ] Add job history filtering and search
- [ ] Add result drill-down pages
- [ ] Add retry button for failed jobs
- [ ] Add export formats beyond plain text
- [ ] Add API tests for the live OCR and agent flows

## Notes

- Local development is PostgreSQL-first. Do not switch the app back to SQLite.
- The remaining major workstreams are OCR, embeddings/vector storage, agents, orchestration, and real compliance rules.
- Keep each new step shippable and testable before moving to the next one.
