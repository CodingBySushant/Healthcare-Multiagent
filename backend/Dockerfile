FROM python:3.11-alpine

WORKDIR /app

# Install build deps for C extensions
RUN apk add --no-cache gcc musl-dev libffi-dev

# Layer-cache: install deps before copying source
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy source
COPY data/     /app/data/
COPY agents/   /app/agents/
COPY backend/  /app/backend/

# Ensure data directory exists for SQLite volume mount
RUN mkdir -p /app/data

ENV PYTHONPATH=/app
ENV DB_PATH=/app/data/healthcare.db

EXPOSE 8000

CMD ["python", "/app/backend/main.py"]
