# Robust Dockerfile with explicit Streamlit installation verification
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install ONLY essential system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p data/uploads output cache

# Set environment variables with explicit PATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PATH="/usr/local/bin:/usr/bin:/bin:$PATH"

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with explicit verification
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt && \
    python -c "import streamlit; print(f'Streamlit version: {streamlit.__version__}')" && \
    which streamlit && \
    streamlit --version

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Health check - verify streamlit is accessible
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD python -c "import streamlit; print('Health check passed')" || exit 1

# Start Streamlit application with explicit python module execution
CMD ["python", "-m", "streamlit", "run", "5-chat.py", "--server.port=8501", "--server.address=0.0.0.0"]