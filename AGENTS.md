# TripWeaver AGENTS.md
## Project
- FastAPI travel itinerary planning backend, Python 3.12+
- Uses uv for dependency management, pytest for testing, ruff for lint/format

## Commands
```bash
# Install all dependencies including dev
uv sync --group dev

# Run all tests
pytest

# Run single test file
pytest tests/test_itineraries.py

# Lint code
ruff check .

# Format code
ruff format .

# Run dev server
uvicorn tripweaver.main:app --reload
```

## Project Structure
- Entrypoint: `src/tripweaver/main.py`
- API Routes: `src/tripweaver/api/routes/`
- Business logic: `src/tripweaver/services/`
- External providers (LLM, search): `src/tripweaver/providers/`
- Pydantic schemas: `src/tripweaver/domain/schemas.py`

## Conventions
- All API routes prefixed with `/api/v1`
- Use dependency injection for providers in services
- Pydantic 2 for all request/response validation
