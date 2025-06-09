FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY payvo-middleware/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy middleware code
COPY payvo-middleware/ .

# Make startup scripts executable
RUN chmod +x start.py simple_start.py

# Expose port
EXPOSE 8000

# Health check - more robust for Railway
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=5 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run the application with simple startup for debugging
CMD ["python", "simple_start.py"] 