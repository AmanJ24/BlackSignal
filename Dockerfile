FROM python:3.12-slim

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

# Download NLP models, then relocate NLTK/textblob's corpora out of /root
# into one of NLTK's standard system-wide search paths (checked regardless of
# which user's $HOME is active) so they're still reachable once the process
# drops to a non-root user below.
RUN python -m spacy download en_core_web_sm && \
    python -m textblob.download_corpora && \
    mkdir -p /usr/local/share/nltk_data && \
    mv /root/nltk_data/* /usr/local/share/nltk_data/ && \
    chmod -R a+rX /usr/local/share/nltk_data

# Copy project files
COPY . .

# Ensure data directories exist
RUN mkdir -p data/raw data/normalized data/enriched data/intelligence logs

# Run as a non-root user. This pipeline parses attacker-controlled content
# scraped from dark web sources, so it shouldn't run as root inside the
# container — that's unnecessary blast radius if a parser is ever exploited.
RUN useradd --create-home --shell /usr/sbin/nologin blacksignal \
    && chown -R blacksignal:blacksignal /app
USER blacksignal

# Expose the dashboard port
EXPOSE 8080

# Default command (can be overridden in docker-compose.yml)
CMD ["python", "web/app.py"]
