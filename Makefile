# Simple developer workflow helpers

PY ?= python3
VENV ?= venv
BIN := $(VENV)/bin
PIP := $(BIN)/pip
FLASK := $(BIN)/flask
PYTHON := $(BIN)/python
# Load environment variables from .env if present
DOTENV := set -a; [ -f .env ] && . ./.env; set +a;

.PHONY: help setup install migrate run run-prod exports-clean seed seed-clean

help:
	@echo "Targets:"
	@echo "  setup          Create venv and install requirements"
	@echo "  install        Install/upgrade requirements into existing venv"
	@echo "  migrate        Run Flask DB migrations (flask db upgrade)"
	@echo "  run            Run the Flask app (debug)"
	@echo "  exports-clean  Remove any locally generated export artifacts (if created)"
	@echo "  seed           Seed a demo project with fields, outcomes, and studies"
	@echo "  seed-clean     Remove the seeded demo project"
	@echo "  project-list   List issues from Projects v2 by Status"

$(BIN)/python:
	$(PY) -m venv $(VENV)

setup: $(BIN)/python
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

install: $(BIN)/python
	$(PIP) install -r requirements.txt

migrate: $(BIN)/python
	$(DOTENV) FLASK_APP=run.py $(FLASK) db upgrade

run: $(BIN)/python
	$(DOTENV) FLASK_DEBUG=1 $(PYTHON) run.py

# Run like production locally (gunicorn, single worker)
run-prod: $(BIN)/python
	$(DOTENV) FLASK_APP=run.py $(FLASK) db upgrade && gunicorn -w 2 -k gthread --threads 4 --timeout 60 --access-logfile - -b 0.0.0.0:8000 wsgi:app

exports-clean:
	@echo "No on-disk export artifacts are created by default; exports stream to client."
	@echo "Nothing to clean."

seed: $(BIN)/python
	$(DOTENV) PYTHONPATH=. FLASK_APP=run.py $(PYTHON) misc/seed_demo.py

seed-clean: $(BIN)/python
	$(DOTENV) PYTHONPATH=. FLASK_APP=run.py $(PYTHON) misc/seed_clean.py

# List items from the user Projects v2 board (requires GH_TOKEN in .env)
project-list: $(BIN)/python
	@if [ -z "$${STATUS}" ]; then echo "STATUS not set (e.g., STATUS=\"In Progress\")"; exit 2; fi;
	$(DOTENV) GH_TOKEN=$${GH_TOKEN} $(PYTHON) scripts/fetch_project_items.py --user ganeshbmc --project 2 --status "$${STATUS}"
