# Changelog — 2025-09-11

## Summary
This session adds robust export features (CSV/Excel and zipped per‑outcome files for both dichotomous and continuous outcomes), richer baseline data entry, project‑level outcome presets, a safer project deletion workflow, and a more flexible setup flow for creating data extraction forms.

## Details

### Exports
- New static fields export for a project:
  - Route: `GET /project/<id>/export_static?format=csv|xlsx`.
  - Buttons added on Project page for CSV and Excel.
- Outcomes (zip) export fixed and expanded:
  - Groups dichotomous outcomes per outcome name; legacy fallback from `dichotomous_outcome` static fields.
  - Adds continuous outcomes per outcome name.
  - Ensures non‑empty ZIP by adding a README when no outcomes exist.
  - Standardized filenames:
    - Dichotomous: `<Project>_<Outcome>_Dichotomous_Export.csv`
    - Continuous: `<Project>_<Outcome>_Continuous_Export.csv`
- Combined export (all data):
  - Route: `GET /project/<id>/export_all_zip`.
  - Includes Static Fields CSV and per‑outcome CSVs for both dichotomous and continuous outcomes using the same naming scheme.

### Data Entry: Baseline Variables
- New field types in Customize Form:
  - `baseline_continuous` (Intervention/Control mean + SD)
  - `baseline_categorical` (Intervention/Control percentage)
- Enter Data UI renders appropriate inputs; autosave and full submit supported.
- Static export expands these into multiple columns.

### Customize Form: Sections and Outcomes
- Section selector now offers existing sections plus an “Add new section…” option.
- Project Outcomes (predefined outcomes) management added:
  - Add/list/delete outcomes with type (dichotomous/continuous).
- Enter Data numerical outcomes revamped:
  - Separate tables for Dichotomous and Continuous.
  - Dropdown to insert predefined outcomes; “Add Selected” and “Add All”.
  - Prevents duplicates, reuses existing empty rows, and shows inline status messages.
  - Dichotomous dropdown correctly hides continuous outcomes.

### Setup Flow
- After choosing SRMA template, user selects one of:
  - Auto‑create base form (as before)
  - Customize now (seed + open builder)
  - Start from scratch (empty builder)
- Guard prevents duplicate template seeding if fields already exist.

### Project Deletion
- New delete route with cascading cleanup and confirmation modal:
  - Requires typing the project name.
  - Shows counts of related studies and fields.
  - Provides “Export all data (zip)” button before delete.

### Models & Migrations
- Added `ProjectOutcome` model to store predefined outcomes by type.
- Added `StudyContinuousOutcome` model for continuous outcomes.
- Migrations added:
  - `ab12cd34ef56_add_project_outcome.py`
  - `bcf12345add6_add_study_continuous_outcome.py`

### Files Updated
- Routes: `app/routes.py`
- Models: `app/models.py`
- Forms: `app/forms.py`
- Utils: `app/utils.py`
- Templates: 
  - `app/templates/project_detail.html`
  - `app/templates/form_fields.html`
  - `app/templates/edit_form_field.html`
  - `app/templates/setup_form.html`
  - `app/templates/enter_data.html`
- Migrations: added new versions listed above
- README: feature list updated for static export

## Notes
- Run DB migrations: `FLASK_APP=run.py flask db upgrade`.
- Exports rely on `pandas` and `openpyxl` (already in `requirements.txt`).
- The legacy `dichotomous_outcome` static field type remains supported for compatibility but numerical outcomes are recommended via the dedicated sections.

---

## Additional Updates (later on 2025-09-11)

- Outcomes zip filename
  - Changed download name to `<Project>_Outcomes_Export.zip` (previously contained “jamovi”).
- Export Outcomes button guard
  - Project page disables the “Export Outcomes (zip)” button with a tooltip when there are no recorded outcomes yet.
- Makefile and scripts
  - Fixed Makefile recipes (tabs and heredoc issues); set `PYTHONPATH=.` for seed scripts.
  - Replaced heredoc-based cleanup with `misc/seed_clean.py`; Make target `seed-clean` runs this script.
  - `seed_clean.py` explicitly deletes studies and form fields before deleting the project to satisfy FK constraints.
  - Added `make_commands.md` documenting all targets and alternative commands.
- Preserve YAML section order + reorder sections
  - New `section_order` field on `CustomFormField` with migration `c1de23a4b567_add_section_order_to_custom_form_field.py`.
  - YAML import sets `section_order` according to template sequence.
  - All field queries now order by `section_order` first, then in‑section `sort_order`.
  - Templates (`form_fields.html`, `enter_data.html`) switched from Jinja `groupby` to pre‑grouped data to avoid accidental re‑sorting.
  - Added section reordering controls (Up/Down) in Customize Form with routes:
    - `POST /project/<id>/form_sections/<section>/move_up`
    - `POST /project/<id>/form_sections/<section>/move_down`
  - Helpers `_normalize_section_orders` and `_move_section` update `section_order` across the section.
