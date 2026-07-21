# Changelog

## [1.0.0] — 2026-07-19

### Added

- **PDF Ingestion Pipeline**: Upload PDF files with automatic validation (extension, magic bytes, size limit), text extraction via PyMuPDF, and metadata extraction (title, author, subject, pages).
- **Recursive Character Chunking**: Split documents into overlapping chunks using a hierarchy of separators (paragraph, sentence, word, character) with configurable chunk size and overlap.
- **Provider-agnostic Embedding System**: Abstract `BaseEmbeddingProvider` interface with full Google Gemini implementation. Ready for BAAI/bge and Ollama providers.
- **Qdrant Vector Store**: Collection auto-creation with cosine similarity. Batch upsert, similarity search, and paper-scoped deletion. Domain-exception translation layer.
- **Hybrid Retrieval**: Reciprocal Rank Fusion combining semantic (vector) search with BM25 keyword search. Configurable top-k, fusion weights, and search modes.
- **Semantic Search**: Query embedding, vector similarity search, chunk lookup, and reordering matching Qdrant rank.
- **BM25 Keyword Search**: Lazy-built BM25 index from PostgreSQL chunk texts using rank-bm25 library. Filters zero-score results.
- **JWT Authentication**: Login, registration, token refresh with httpOnly cookies, route guards, and Axios interceptor auto-refresh.
- **Next.js Frontend**: Dashboard, Upload, Library, Search, PDF Viewer, and Settings pages.
- **Responsive Design**: Adaptive layouts for mobile, tablet, and desktop with collapsible sidebar, preview panel, and full-screen viewer.
- **Dark Mode**: Full dark/light theme support persisted to localStorage.
- **Modern UI**: shadcn/ui components, Framer Motion animations, Sonner toasts, skeleton loading states, and empty states.
- **Docker Deployment**: Multi-stage Dockerfiles for backend and frontend. Production docker-compose with health checks and persistent volumes.
- **Database Migrations**: Alembic-managed schema with automated migration execution.
- **Comprehensive Error Handling**: Domain-exception hierarchy, FastAPI exception handlers, and user-friendly error displays.
- **Testing**: 236 backend tests (unit + integration) covering the complete indexing and retrieval pipeline.

### Changed

- Based on existing codebase architecture; no breaking changes.

### Security

- JWT tokens signed with configurable secret key and algorithm.
- Passwords hashed with bcrypt via passlib.
- Refresh tokens stored in httpOnly, SameSite=Lax cookies.
- CORS configured with explicit allow-list.
- PDF validation against extension, magic bytes, and size limits.
- File path traversal protection with `Path.relative_to()`.

### Notes

- Production deployments **must** set `SECRET_KEY` to a strong random value.
- `GEMINI_API_KEY` is required for embedding generation.
- See `.env.example` for all configuration options.
