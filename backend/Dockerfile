FROM python:3.11-slim

WORKDIR /app

# System deps for WeasyPrint/Pango and PostgreSQL client
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e "."

COPY . .
RUN chmod +x entrypoint-render.sh

EXPOSE 8000

# Default command: production Uvicorn (no --reload).
# Override in docker-compose for local dev (uvicorn ... --reload).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
