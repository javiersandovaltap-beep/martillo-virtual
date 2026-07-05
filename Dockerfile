# Multi-stage Dockerfile for MartilloVirtual
# LEARNING EXERCISE - NOT USED FOR RENDER DEPLOY
# Render free tier does not support Docker. Deploy uses Procfile instead.
#
# To build locally:
#   docker build -t martillo-virtual .
# To run locally:
#   docker run -p 8000:8000 --env-file .env martillo-virtual
# To run tests in container:
#   docker run --env-file .env martillo-virtual python -m pytest subastas/tests/

# === Builder stage: install dependencies ===
FROM python:3.14-slim AS builder

# Build dependencies for psycopg and Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies to /root/.local (user site)
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# === Runtime stage: minimal image ===
FROM python:3.14-slim AS runtime

# Runtime dependencies (libpq5 for psycopg, no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Copy project files
COPY . .

# Collect static files (needed for WhiteNoise in production)
RUN python manage.py collectstatic --noinput

# Expose port (Render sets $PORT env var, we use 8000 as default)
EXPOSE 8000

# Health check (optional, Render can use it)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run gunicorn (production WSGI server)
# Note: Render uses Procfile `web: gunicorn config.wsgi ...` for actual deploy.
# This CMD is for local Docker testing only.
CMD ["gunicorn", "config.wsgi", "--workers", "2", "--bind", "0.0.0.0:8000", "--timeout", "120"]
