# Multi-stage build for smaller final image
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies needed for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY src/ ./src/
COPY main.py .

# Ensure scripts are in PATH
ENV PATH=/root/.local/bin:$PATH

# Create output directory
RUN mkdir -p data/output data/logs

# Run as non-root user for security
RUN useradd -m -u 1000 podcast && chown -R podcast:podcast /app
USER podcast

# Cloud Run will provide PORT, but we'll use a script entrypoint
CMD ["python", "main.py"]
