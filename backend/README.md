# ResearchMind AI Backend

Enterprise-grade Retrieval-Augmented Generation (RAG) platform for scientific literature.

## Tech Stack

- **FastAPI** — Async web framework with automatic OpenAPI docs
- **SQLAlchemy 2.0** — ORM with repository pattern
- **PostgreSQL 17** — Relational database for chunk storage
- **Qdrant** — Vector database for semantic similarity search
- **PyMuPDF (fitz)** — PDF text extraction
- **Gemini API** — Text embeddings (768-dim)
- **rank-bm25** — Keyword retrieval
- **Alembic** — Database migrations

## Development

### Prerequisites

- Python 3.13+
- Docker Desktop
- uv (recommended) or pip

### Setup

```bash
# Start infrastructure
docker compose up -d

# Install dependencies
uv sync

# Run migrations
uv run alembic upgrade head

# Start the server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required variables:
- `GEMINI_API_KEY` — Google Gemini API key for embeddings
- `SECRET_KEY` — JWT signing secret (generate with `python -c "import secrets; print(secrets.token_hex(32))"`)

### Running Tests

```bash
# All tests (requires PostgreSQL + Qdrant running)
uv run pytest -v

# Unit tests only
uv run pytest tests/ -v --ignore=tests/integration

# Integration tests only
uv run pytest tests/integration/ -v
```

### Lint & Type Check

```bash
uv run ruff check .
uv run mypy app/ --ignore-missing-imports
```

## Docker

```bash
# Build the image
docker build -t researchmind-backend .

# Run with docker compose
docker compose -f docker-compose.prod.yml up -d
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health: http://localhost:8000/health

### Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Login and receive JWT tokens |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/health` | Liveness check with database status |
| GET | `/ready` | Readiness probe (for orchestration) |
| GET | `/version` | Application version |
| GET | `/stats` | Application statistics |
| POST | `/papers/upload` | Upload a PDF paper |
| GET | `/papers` | List papers (paginated) |
| GET | `/papers/{id}` | Get paper details |
| DELETE | `/papers/{id}` | Delete a paper |
| GET | `/search` | Hybrid search (semantic + BM25) |
| GET | `/search/semantic` | Semantic-only search |
| GET | `/search/keyword` | BM25-only search |
