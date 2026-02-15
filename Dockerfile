FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r /app/requirements.txt

# Copy app
COPY . /app

RUN chmod +x /app/main.py || true

VOLUME ["/app/data", "/app/clips", "/app/logs"]

# Create data directories
RUN mkdir -p /app/data /app/clips /app/logs

ENTRYPOINT ["python", "/app/main.py"]
