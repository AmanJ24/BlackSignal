FROM python:3.10-slim

# Install system dependencies (needed for compiling some python packages and basic tools)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download NLP models required by the pipeline
RUN python -m spacy download en_core_web_sm && \
    python -m textblob.download_corpora

# Copy project files
COPY . .

# Ensure data directories exist
RUN mkdir -p data/raw data/normalized data/enriched data/intelligence logs

# Expose the dashboard port
EXPOSE 8080

# Default command (can be overridden in docker-compose.yml)
CMD ["python", "web/app.py"]
