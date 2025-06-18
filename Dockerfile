FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project structure
COPY . .

# Make sure main.py and run.py are executable
RUN chmod +x main.py
RUN chmod +x middleware-system/run.py

# Expose port 8000 for the application
EXPOSE 8000

# Use the main.py entry point
CMD ["python", "main.py"] 