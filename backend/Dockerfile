# Sahayak backend — FastAPI on a slim Python image.
# Build from the REPO ROOT so /shared is in context:
#   docker build -f backend/Dockerfile -t sahayak-api .
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
# The shared scheme/form/i18n data is the source of truth (config resolves /shared).
COPY shared /shared

EXPOSE 8000
# Honour the platform's $PORT (App Runner/Cloud Run set it); default 8000.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
