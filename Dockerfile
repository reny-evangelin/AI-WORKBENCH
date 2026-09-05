FROM python:3.13-slim

WORKDIR /app

# Install system build dependencies and curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy repository content
COPY . .

# Ensure required directories exist
RUN mkdir -p outputs chroma_db data/documents

EXPOSE 8080

CMD ["python", "startup.py"]
