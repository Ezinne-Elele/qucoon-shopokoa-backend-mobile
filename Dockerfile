FROM python:3.11-slim

# Avoid issues with pip warnings + faster builds
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Copy global-bundle.pem if it exists (required for DocumentDB)
# Note: This file should be in the mobile-backend directory or copied from parent during build
COPY global-bundle.pem* ./

# Expose port
EXPOSE 5002

# Run with Gunicorn using Uvicorn workers for production
CMD ["gunicorn", "--bind", "0.0.0.0:5002", "--workers", "2", "--timeout", "60", "-k", "uvicorn.workers.UvicornWorker", "app:app"]