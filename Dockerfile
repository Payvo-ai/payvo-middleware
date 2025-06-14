FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY middleware-system/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy middleware code
COPY middleware-system/ .

# Make startup scripts executable
RUN chmod +x start.py simple_start.py run.py

# Expose port 8000 for the application
EXPOSE 8000

# Use the robust startup script
CMD ["python", "start.py"] 