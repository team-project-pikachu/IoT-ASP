# Cloud Run image for iot-asp-ingest (#61). Build context = this directory.
FROM python:3.12-slim-bookworm

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    GOOGLE_CLOUD_PROJECT=bear-iot-asp-rec

COPY requirements-ingest.txt ./
RUN pip install --no-cache-dir -r requirements-ingest.txt

COPY iot_asp_autoroute ./iot_asp_autoroute
COPY ingest_app.py ./

# Non-root
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080
CMD exec gunicorn --bind ":${PORT}" --workers 1 --threads 8 --timeout 120 ingest_app:app
