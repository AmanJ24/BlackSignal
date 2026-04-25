# ==========================================
# BlackSignal Makefile
# ==========================================

VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: help install run web test clean docker-build docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make install      - Create virtual environment and install dependencies + models"
	@echo "  make run          - Run the BlackSignal pipeline (CLI)"
	@echo "  make web          - Run the BlackSignal web dashboard"
	@echo "  make test         - Run the test suite"
	@echo "  make clean        - Remove caches and virtual environment"
	@echo "  make docker-build - Build the Docker images"
	@echo "  make docker-up    - Run the project via Docker Compose"
	@echo "  make docker-down  - Stop the Docker containers"

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt
	@touch $(VENV)/bin/activate

.setup_done: $(VENV)/bin/activate
	@echo "🚀 Starting Dark Web OSINT Platform Setup..."
	@echo "🧠 Downloading NLP Models (spaCy & TextBlob)..."
	$(PYTHON) -m spacy download en_core_web_sm
	$(PYTHON) -m textblob.download_corpora
	@echo "📂 Creating Data Directory Structure..."
	mkdir -p data/raw data/normalized data/enriched data/intelligence logs
	@echo "✅ Setup Complete!"
	@touch .setup_done

install: .setup_done

run: install
	$(PYTHON) orchestration/run_pipeline.py

web: install
	$(PYTHON) web/app.py

test: install
	$(PYTHON) -m pytest tests/ -v

clean:
	rm -rf $(VENV)
	rm -rf __pycache__ .pytest_cache
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down
