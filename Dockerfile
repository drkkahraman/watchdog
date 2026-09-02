FROM python:3.11-slim

LABEL maintainer="Watchdog Contributors"
LABEL description="Real-time Docker & Service Status Monitor (TUI)"

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY watchdog/ ./watchdog/

RUN pip install --no-cache-dir .

ENV PYTHONUNBUFFERED=1
ENV TERM=xterm-256color

ENTRYPOINT ["watchdog"]
