# syntax=docker/dockerfile:1.7
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv

# pizza-core comes from the private Artifact Registry Python repo (gcp repo: envs/shared).
# CI passes a short-lived OAuth access token as a BuildKit secret, see .github/workflows/ci.yml.
ARG PYTHON_INDEX=europe-central2-python.pkg.dev/pizza-shared-4821/python-libs/simple/

COPY pyproject.toml ./
COPY app ./app
RUN --mount=type=secret,id=ar_token \
    pip install --extra-index-url "https://oauth2accesstoken:$(cat /run/secrets/ar_token)@${PYTHON_INDEX}" .

# used by the pizza-backend-migrate Cloud Run job: alembic upgrade head
COPY alembic.ini ./
COPY migrations ./migrations

RUN useradd --create-home --uid 10001 app
USER app

# Cloud Run sends traffic to $PORT (container_port = 8080 in the gcp repo)
ENV PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
