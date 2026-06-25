# ── Build stage ──────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

COPY pyproject.toml .
RUN pip install --no-cache-dir --user .

# ── Production stage ─────────────────────────
FROM python:3.12-slim

RUN groupadd -r openpaper && useradd -r -g openpaper -d /app -s /bin/false openpaper

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:$PATH" \
    PYTHONPATH="/root/.local/lib/python3.12/site-packages:$PYTHONPATH"

COPY --from=builder /root/.local /root/.local

COPY --chown=openpaper:openpaper . .

USER openpaper

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/api/v1/health/live', timeout=5).raise_for_status()"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
