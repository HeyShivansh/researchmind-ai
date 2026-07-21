#!/bin/sh
# =============================================================================
# ResearchMind AI — Backend Entrypoint
# =============================================================================
# This script runs before the application starts:
#   1. Wait for PostgreSQL to be ready
#   2. Apply pending database migrations (alembic upgrade head)
#   3. Start the uvicorn server
# =============================================================================

set -e

echo "==> Waiting for PostgreSQL to be ready..."
for i in 1 2 3 4 5 6 7 8 9 10; do
  if python -c "from app.database.session import engine; engine.connect()" 2>/dev/null; then
    echo "==> PostgreSQL is ready."
    break
  fi
  echo "==> Attempt $i/10: PostgreSQL not ready, waiting..."
  sleep 6
done

echo "==> Running database migrations..."
alembic upgrade head
echo "==> Migrations complete."

echo "==> Starting uvicorn server..."
exec uvicorn app.main:app \
    --host "${HOST:-0.0.0.0}" \
    --port "${PORT:-8000}" \
    --workers "${UVICORN_WORKERS:-4}" \
    --limit-max-requests "${UVICORN_LIMIT_MAX_REQUESTS:-10000}" \
    --timeout-keep-alive "${UVICORN_TIMEOUT_KEEP_ALIVE:-30}" \
    --proxy-headers
