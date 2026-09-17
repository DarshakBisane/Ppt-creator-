# ==============================================================================
# Production Dockerfile for AI Presentation Generator (Backend Service)
# Multi-stage / Minimal Debian-slim with non-root security and font determinism
# ==============================================================================

ARG PYTHON_VERSION=3.14-slim
FROM python:${PYTHON_VERSION} AS runtime

# 1. System dependencies:
# - fonts-dejavu-core / fonts-liberation: deterministic font metrics for Pillow layout engine
# - curl: lightweight health checking
# - ca-certificates: secure HTTPS egress for Gemini API
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core \
    fonts-liberation \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 2. Configure container execution environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    ENVIRONMENT=production

# 3. Create unprivileged non-root user and group
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /sbin/nologin -M appuser

WORKDIR /app

# 4. Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# 5. Copy backend application source code only
COPY app /app/backend/app

# 6. Initialize sandboxed artifact storage directory with appropriate non-root ownership
RUN mkdir -p /app/temp/artifacts && \
    chown -R appuser:appgroup /app/temp

# 7. Switch to non-root runtime user
USER appuser:appgroup

# 8. Expose default service port
EXPOSE 8000

# 9. Lightweight Docker Health Check against /health endpoint
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://127.0.0.1:${API_PORT}/health || exit 1

# 10. Production Server Startup
# NOTE: Uses single worker process (--workers 1) to preserve process-local MemoryJobStore consistency.
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
