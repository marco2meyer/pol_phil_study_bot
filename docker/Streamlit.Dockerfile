# Generic Streamlit Dockerfile for multi-bot
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy app code
COPY . .

# Install Python deps (per-bot only; root requirements.txt removed)
RUN pip install --upgrade pip
ARG BOT_REQ=
RUN if [ -n "$BOT_REQ" ] && [ -f "$BOT_REQ" ]; then \
      echo "Installing bot-specific requirements from $BOT_REQ" && \
      pip install -r "$BOT_REQ" ; \
    else \
      echo "No bot-specific requirements provided" ; \
    fi

# Streamlit config
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_HEADLESS=true

EXPOSE 8501

# Defaults (override via compose)
ENV PORT=8501 \
    OPENAI_MODEL=gpt-5 \
    APP_PATH=app.py \
    BASE_URL_PATH=

# Entrypoint: support sub-URL base path
CMD ["bash", "-lc", "streamlit run \"${APP_PATH}\" --server.address=0.0.0.0 --server.port=8501 ${BASE_URL_PATH:+--server.baseUrlPath=/\"${BASE_URL_PATH}\"}"]
