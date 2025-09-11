# Simple developer workflow helpers

PY ?= python3
VENV ?= venv
BIN := $(VENV)/bin
PIP := $(BIN)/pip
FLASK := $(BIN)/flask
PYTHON := $(BIN)/python

.PHONY: help setup install migrate run exports-clean seed seed-clean

help:
	@echo "Targets:"
	@echo "  setup          Create venv and install requirements"
	@echo "  install        Install/upgrade requirements into existing venv"
	@echo "  migrate        Run Flask DB migrations (flask db upgrade)"
	@echo "  run            Run the Flask app (debug)"
	@echo "  exports-clean  Remove any locally generated export artifacts (if created)"
	@echo "  seed           Seed a demo project with fields, outcomes, and studies"
	@echo "  seed-clean     Remove the seeded demo project"

$(BIN)/python:
	$(PY) -m venv $(VENV)

setup: $(BIN)/python
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

install: $(BIN)/python
	$(PIP) install -r requirements.txt

migrate: $(BIN)/python
	FLASK_APP=run.py $(FLASK) db upgrade

run: $(BIN)/python
	$(PYTHON) run.py

exports-clean:
	@echo "No on-disk export artifacts are created by default; exports stream to client."
	@echo "Nothing to clean."

seed: $(BIN)/python
	PYTHONPATH=. FLASK_APP=run.py $(PYTHON) misc/seed_demo.py

seed-clean: $(BIN)/python
	PYTHONPATH=. FLASK_APP=run.py $(PYTHON) misc/seed_clean.py
