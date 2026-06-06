web: cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT
worker: cd backend && uv run python -m app.worker.runner
