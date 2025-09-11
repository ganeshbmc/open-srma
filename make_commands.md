# Make Commands Guide

This project includes a Makefile to streamline common developer tasks. Below are the available targets and equivalent commands you can run directly without `make`.

## Prerequisites
- Python 3.10+ recommended
- Optional virtual environment (recommended):
  - macOS/Linux: `python3 -m venv venv && source venv/bin/activate`
  - Windows (PowerShell): `python -m venv venv; .\\venv\\Scripts\\Activate.ps1`

## Targets and Alternatives

- help
  - Description: List available make targets.
  - Run: `make help`
  - Alternative: Open `Makefile` to see targets.

- setup
  - Description: Create a virtualenv and install dependencies.
  - Run: `make setup`
  - Alternative:
    - `python3 -m venv venv`
    - `source venv/bin/activate`
    - `pip install --upgrade pip`
    - `pip install -r requirements.txt`

- install
  - Description: Install requirements into an existing venv.
  - Run: `make install`
  - Alternative:
    - `source venv/bin/activate`
    - `pip install -r requirements.txt`

- migrate
  - Description: Apply database migrations (Alembic via Flask-Migrate).
  - Run: `make migrate`
  - Alternatives:
    - `export FLASK_APP=run.py && flask db upgrade` (macOS/Linux)
    - `$env:FLASK_APP="run.py"; flask db upgrade` (Windows PowerShell)

- run
  - Description: Start the Flask development server.
  - Run: `make run`
  - Alternatives:
    - `python3 run.py`
    - `export FLASK_APP=run.py && flask run` (uses Flask’s CLI)

- seed
  - Description: Seed a demo project ("Demo SRMA") with fields, outcomes, and studies for quick testing.
  - Run: `make seed`
  - Alternative (from repo root, after activating venv):
    - macOS/Linux: `PYTHONPATH=. FLASK_APP=run.py python3 misc/seed_demo.py`
    - Windows PowerShell: `$env:PYTHONPATH='.'; $env:FLASK_APP='run.py'; python misc/seed_demo.py`

- seed-clean
  - Description: Remove the seeded demo project and its related data.
  - Run: `make seed-clean`
  - Alternative:
    - macOS/Linux: `PYTHONPATH=. FLASK_APP=run.py python3 misc/seed_clean.py`
    - Windows PowerShell: `$env:PYTHONPATH='.'; $env:FLASK_APP='run.py'; python misc/seed_clean.py`

- exports-clean
  - Description: No-op. Exports are streamed to the client; nothing is written locally by default.
  - Run: `make exports-clean`

## Notes
- If imports fail when running scripts in `misc/`, ensure the repo root is on `PYTHONPATH` (as shown above).
- Before running `seed` or `seed-clean`, apply migrations with `make migrate`.
- For CSRF-protected routes (e.g., autosave), ensure the app runs through `run.py` or with `FLASK_APP=run.py`.
