FROM python:3.14.7-slim AS builder

WORKDIR /myapp

RUN python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.14.7-slim AS runtime

RUN groupadd --system --gid 1001 appuser \
    && useradd --system --uid 1001 --gid 1001 appuser

WORKDIR /myapp

COPY --from=builder /opt/venv /opt/venv

COPY app.py .

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 5000

USER appuser

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]