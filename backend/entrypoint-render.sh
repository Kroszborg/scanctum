#!/bin/sh
# Used on Render: rewrite postgresql:// to postgresql+asyncpg:// and +psycopg2://
# (Render Blueprint cannot transform env vars; this runs before the app.)
if [ -n "$DATABASE_URL" ]; then
  export DATABASE_URL=$(echo "$DATABASE_URL" | sed 's|^postgresql://|postgresql+asyncpg://|')
fi
if [ -n "$DATABASE_URL_SYNC" ]; then
  export DATABASE_URL_SYNC=$(echo "$DATABASE_URL_SYNC" | sed 's|^postgresql://|postgresql+psycopg2://|')
fi
set -e
alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 2
