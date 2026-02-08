# syntax=docker/dockerfile:1

# Stage 1: Build (compile C extensions that need g++)
FROM python:3.11-slim AS builder

RUN --mount=type=cache,id=apt-cache-builder,target=/var/cache/apt \
    --mount=type=cache,id=apt-lists-builder,target=/var/lib/apt/lists \
    apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    espeak-ng \
    g++

WORKDIR /app

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefix=/install -r requirements.txt

# Stage 2: Runtime (no g++, no build tools)
FROM python:3.11-slim

RUN --mount=type=cache,id=apt-cache-runtime,target=/var/cache/apt \
    --mount=type=cache,id=apt-lists-runtime,target=/var/lib/apt/lists \
    apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    espeak-ng

WORKDIR /app

COPY --from=builder /install /usr/local

ENTRYPOINT ["python", "-m", "tts_app.cli"]
