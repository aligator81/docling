# Optimized Dockerfile for Coolify compatibility with cmake support
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including cmake for pyarrow compilation
RUN apt-get update && apt-get install -y \
    curl \
    git \
    cmake \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies - allow binary packages where possible
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/uploads output cache

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose Streamlit port
EXPOSE 8501

# Health check - check if Streamlit is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Start Streamlit application
CMD ["streamlit", "run", "5-chat.py", "--server.port=8501", "--server.address=0.0.0.0"]