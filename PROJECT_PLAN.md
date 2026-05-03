# Project Plan and Milestones

## Done

- [x] Setup repository structure and scaffolding
- [x] Create backend FastAPI service with upload, status, and result endpoints
- [x] Add database persistence for document jobs and results
- [x] Implement async background processing with FastAPI background tasks
- [x] Build the React frontend shell for dashboard, upload, and results views
- [x] Restore the mockup-faithful frontend layout and interactions
- [x] Integrate the frontend with live backend upload, status polling, and result rendering
- [x] Add backend dashboard summary endpoint for real job stats and recent activity
- [x] Add deterministic text parsing for text, HTML, and DOCX files without AI dependencies
- [x] Add backend-generated metadata, issues, and score payloads for the frontend
- [x] Default local persistence to SQLite while keeping `DATABASE_URL` override support

## Next Backend Tasks

- [ ] Add true PDF text extraction instead of placeholder summaries
- [ ] Add image OCR pipeline for PNG/JPG/TIFF uploads
- [ ] Add XLSX parsing for sheet previews and extracted cell content
- [ ] Store structured result metadata and issues in dedicated database columns
- [ ] Add API tests for upload, status, result, and dashboard endpoints
- [ ] Add failure handling and retry-safe status updates for background jobs
- [ ] Add file validation rules for unsupported formats and oversized uploads

## OCR and Extraction Backlog

- [ ] Evaluate Tesseract for local OCR quality and performance
- [ ] Evaluate PaddleOCR as an alternative OCR backend
- [ ] Add OCR preprocessing for rotation, denoise, and contrast normalization
- [ ] Add page-level OCR progress tracking
- [ ] Add confidence scores to extracted entities
- [ ] Add parser selection by file type and MIME type

## Compliance and Reasoning Backlog

- [ ] Define the first real compliance rule set and rule output schema
- [ ] Replace heuristic issues with actual compliance checks
- [ ] Add document classification before compliance evaluation
- [ ] Add explanation fields for every compliance finding
- [ ] Add audit trail storage for rule execution steps

## Retrieval and Vector Backlog

- [ ] Define chunking strategy for uploaded documents
- [ ] Add embeddings provider abstraction
- [ ] Choose initial vector store implementation
- [ ] Store document chunks with metadata filters
- [ ] Add retrieval endpoint for related clauses and prior documents
- [ ] Add reranking step for retrieved context

## Agent and LangGraph Backlog

- [ ] Define agent responsibilities and handoff contracts
- [ ] Add tool interfaces for regulation lookup and prior-case search
- [ ] Build a LangGraph orchestration prototype for document flow
- [ ] Add retry and fallback branches for failed agent steps
- [ ] Add structured trace output for every orchestrated run

## Platform Backlog

- [ ] Add authentication and role-based access control
- [ ] Add per-user document ownership and history
- [ ] Add frontend filters, search, and recent job drill-down
- [ ] Add export formats beyond plain text reports
- [ ] Add observability for latency, failures, and processing throughput
- [ ] Add CI checks for backend and frontend builds
- [ ] Add Docker-based local startup

## Notes

Keep tasks small and concrete. Only mark items done when they are implemented in code and visible in the app or API.
