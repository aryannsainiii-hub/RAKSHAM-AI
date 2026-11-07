# Development

Run API from repository root with `python -m uvicorn app.main:app --app-dir backend --reload --port 8000`; frontend with `cd frontend; npm run dev`. OpenAPI is generated from FastAPI schemas at `/docs`.

SQLite is created automatically; choose a different file with `RAKSHAM_DB_PATH`. If the UI reports backend unavailable, check the API health route and `VITE_API_URL`. Browser requests default to localhost:8000. Restrict `RAKSHAM_CORS_ORIGINS` before deployment. Do not expose the write-capable demo API to public traffic as-is.

The deterministic screening benchmark is `python scripts/benchmark_screening.py`. Keep fixture inputs fixed when comparing runs. Frontend assets should be checked with `npm run build`.
