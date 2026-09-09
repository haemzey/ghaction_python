# ---- Build stage ----
FROM python:3.12.7-slim AS builder

WORKDIR /myapp

RUN apt-get update && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# ---- Runtime stage ----
FROM python:3.12.7-slim

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /myapp

COPY --from=builder /opt/venv /opt/venv

COPY app.py .

# SQLite needs a writable location for its .db file.
RUN mkdir -p /myapp/data && chown -R appuser:appuser /myapp/data

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

USER appuser

CMD ["python", "app.py"]