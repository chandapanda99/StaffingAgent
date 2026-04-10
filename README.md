# Email Intake Matcher

Production-friendly Python scaffold for an email intake and matching application. The current codebase provides clean architecture, typed interfaces, storage/persistence boundaries, and placeholder workflow endpoints. It does not implement business logic yet.

## Stack

- FastAPI for the HTTP API
- PostgreSQL + SQLAlchemy + Alembic for persistence
- Pydantic v2 for settings, API schemas, and domain DTOs
- Microsoft Graph adapter boundary for Outlook mailbox access
- S3-compatible object storage boundary with MinIO for local development
- OpenAI-oriented adapter placeholder behind provider interfaces

## Project Layout

```text
app/
  api/            HTTP routes, dependencies, request/response schemas
  core/           settings, logging, exceptions
  db/             engine, sessions, ORM models, repositories
  domain/         shared enums and Pydantic models
  integrations/   Outlook, storage, and LLM provider adapters
  services/       business-facing service interfaces and orchestrators
  workflows/      intake, classification, extraction, matching stubs
tests/            API and contract tests
alembic/          migrations
```

## Local Setup

1. Copy `.env.example` to `.env`.
2. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

3. Start local infrastructure:

```bash
docker compose up -d postgres minio
```

4. Run the initial migration:

```bash
alembic upgrade head
```

5. Start the API:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`, and the OpenAPI docs at `http://localhost:8000/docs`.

## Docker Compose

To run the app and dependencies together:

```bash
cp .env.example .env
docker compose up --build
```

## Tests

```bash
pytest
```

## Current Endpoints

- `GET /health`
- `GET /ready`
- `POST /emails/intake`
- `POST /messages/{message_id}/classify`
- `POST /messages/{message_id}/extract`
- `POST /matches/run`
- `GET /matches/{match_run_id}`

These endpoints intentionally return placeholder responses while preserving future-friendly contracts.

## Outlook Integration Note

The scaffold targets Microsoft Graph for Outlook mailbox access. The Graph adapter is an interface boundary with a stub implementation so the app structure is ready before credentials and ingestion logic are added.
