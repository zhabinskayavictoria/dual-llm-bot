FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml ./
RUN uv venv && \
    . .venv/bin/activate && \
    uv pip install --no-cache -e .

COPY . .

ENV PATH="/app/.venv/bin:$PATH"
