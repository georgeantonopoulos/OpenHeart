#!/bin/bash
set -e

echo "============================================"
echo "OpenHeart Cyprus - Backend Startup"
echo "Environment: ${ENVIRONMENT:-development}"
echo "============================================"

# Step 1: Run Alembic migrations
echo ""
echo "[1/3] Running database migrations..."
alembic upgrade head
echo "Migrations complete."

# Step 2: Seed development data (only in development)
if [ "${ENVIRONMENT}" = "development" ]; then
    echo ""
    echo "[2/3] Seeding development data..."
    python -m app.core.seed
    echo "Seed complete."
else
    echo ""
    echo "[2/3] Skipping seed (not development environment)"
fi

# Step 3: Start the application
echo ""
echo "[3/3] Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
