FROM python:3.12-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LICENSE_SERVER_HOST=0.0.0.0 \
    LICENSE_SERVER_PORT=8195

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY templates ./templates
COPY static ./static
COPY alembic ./alembic
COPY alembic.ini .
COPY docker/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh && mkdir -p /app/data

EXPOSE 8195

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS "http://127.0.0.1:${LICENSE_SERVER_PORT:-8195}/health" || exit 1

VOLUME ["/app/data"]

ENTRYPOINT ["/entrypoint.sh"]
