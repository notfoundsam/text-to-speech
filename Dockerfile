FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    espeak-ng \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install base dependencies (PyTorch - large, rarely changes)
COPY requirements-base.txt .
RUN pip install --no-cache-dir -r requirements-base.txt

# Install app dependencies (smaller, may change more often)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "-m", "tts_app.cli"]
