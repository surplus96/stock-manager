# Hugging Face Spaces — Docker SDK runtime for the FastAPI backend.
# HF Spaces routes external HTTPS to ${PORT} (defaults to 7860).
# Reviewers hit https://huggingface.co/spaces/<user>/stock-manager-api
# directly — no key entry required (server-side env vars handle auth).

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=7860 \
    HF_HOME=/tmp/hf_cache \
    XDG_CACHE_HOME=/tmp/.cache \
    MPLCONFIGDIR=/tmp/matplotlib

# Build deps for pandas/numpy wheels and lxml (DART XBRL parsing).
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libxml2-dev \
        libxslt1-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# HF Spaces runs as a non-root user (UID 1000); make writable dirs that
# diskcache + matplotlib + huggingface need.
RUN mkdir -p /tmp/diskcache /tmp/hf_cache /tmp/.cache /tmp/matplotlib \
    && chmod -R 777 /tmp

EXPOSE 7860

CMD ["sh", "-c", "uvicorn api.server:app --host 0.0.0.0 --port ${PORT:-7860}"]
