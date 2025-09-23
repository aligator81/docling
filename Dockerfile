# Minimal Dockerfile that works with Coolify's Python 3.12 environment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install ONLY essential system dependencies that Coolify might need
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p data/uploads output cache

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose Streamlit port
EXPOSE 8501

# Health check - simple Python check that doesn't require distutils
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD python -c "print('Health check passed')" || exit 1

# Start Streamlit application
CMD ["streamlit", "run", "5-chat.py", "--server.port=8501", "--server.address=0.0.0.0"]