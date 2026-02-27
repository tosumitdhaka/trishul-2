# Stage 1: build dependencies
FROM python:3.12-slim AS builder
WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install .

# Stage 2: runtime
FROM python:3.12-slim
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY core/       ./core/
COPY transformer/ ./transformer/
COPY plugins/    ./plugins/

# Non-root user
RUN adduser --disabled-password --gecos "" trishul
USER trishul

# Persistent data directory (SQLite volume mount point)
VOLUME ["/data"]

EXPOSE 8000

CMD ["uvicorn", "core.app:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--no-access-log"]
