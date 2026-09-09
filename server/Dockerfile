# ---- Build stage ----
FROM python:3.12.7-slim AS builder

WORKDIR /myapp

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

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["python", "app.py"]