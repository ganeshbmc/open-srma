# Upgrade Steps — 2025-09-11

These steps upgrade your local environment and verify today’s changes.

## Prerequisites
- Python 3.10+ and virtualenv (recommended)
- From repo root: `open-srma/`

## Install & Migrate
1. Create and activate a virtual environment (optional):
   - `python3 -m venv venv`
   - `source venv/bin/activate`
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Apply database migrations:
   - `export FLASK_APP=run.py`
   - `flask db upgrade`
4. Verify migration state (optional):
   - `flask db current` (should show latest revision)

## Quick Smoke Test
1. Run the app:
   - `python run.py` (browse to http://127.0.0.1:5000/)
2. Create a project and try setup options:
   - Auto-create base form
   - Customize now (opens builder, fields seeded)
   - Start from scratch (empty builder)
   - Revisit setup with existing fields → no duplicate seeding
3. Customize Form:
   - Add a few fields, including `Baseline: Continuous` and `Baseline: Categorical`
   - Add Project Outcomes: one Dichotomous and one Continuous
4. Enter Data for a study:
   - Fill baseline continuous/categorical values (both groups). Confirm autosave per section shows “Saved at …”
   - Dichotomous outcomes: use “Add Selected” (reuses empty row) and “Add All” (no duplicates)
   - Continuous outcomes: same as above
   - Click “Save All Data”
5. Exports:
   - Static fields: click CSV and Excel on Project page; confirm baseline columns appear
   - Outcomes (zip): confirm per-outcome CSVs for dichotomous and continuous
     - Filenames: `<Project>_<Outcome>_Dichotomous_Export.csv` and `_Continuous_Export.csv`
   - Export all data (zip): includes static CSV and per-outcome CSVs for both types with the same naming scheme
6. Project deletion:
   - Open Delete Project modal → click “Export all data (zip)”, then confirm delete by typing project name
   - Verify redirect to Projects with a success flash

## Notes
- If autosave requests fail in dev, ensure CSRF token is present (meta tag in `base.html`) and that the server logs show POSTs to `/autosave` being accepted.
- Migrations added today:
  - `ab12cd34ef56_add_project_outcome.py`
  - `bcf12345add6_add_study_continuous_outcome.py`
- Legacy `dichotomous_outcome` static fields remain supported but prefer the dedicated outcomes tables.
