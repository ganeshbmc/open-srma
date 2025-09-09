# Changelog — 2025-09-10

## Summary
This release improves form usability and visual consistency, and adds quality-of-life features for data entry:

- Grouped fields under each section header (no repeated headers)
- Visual refresh across pages using Bootstrap (navbar, cards, list-groups)
- Collapsible sections on the data entry page
- Per‑section Save buttons with status badges
- Autosave for each section (debounced) and for numerical outcomes
- Global "Last saved at" timestamp in a sticky footer
- Field help tooltips driven by a new `help_text` attribute
- Stable ordering of fields by section and in‑section order
- New autosave API endpoint
- Database migrations updated and migration head conflict resolved

## Details

### UI/Template Changes
- Grouped section rendering so each header appears once, with all fields beneath:
  - `app/templates/form_fields.html`
  - `app/templates/enter_data.html`
- Bootstrap visual improvements:
  - `app/templates/base.html`: Added navbar
  - `app/templates/index.html`: Projects as list-group with Add Project
  - `app/templates/project_detail.html`: Studies in a card with actions
  - `app/templates/form_fields.html`: Sections inside cards with compact tables
  - `app/templates/enter_data.html`: Sections as cards; inputs styled with `form-control`
- Collapsible sections in data entry with per‑section Save buttons and status indicators
- Numerical outcomes redesigned to an editable table with Add/Remove row
- Sticky bottom action bar with Save/Back and global "Last saved at" timestamp

### Autosave
- New JSON endpoint to persist partial changes:
  - `POST /project/<project_id>/study/<study_id>/autosave`
  - Supports saving a single section of static fields or replacing numerical outcomes table rows
- Data entry page (`enter_data.html`) now:
  - Debounces autosave (1s) on input/change events per section
  - Autosaves numerical outcomes on any edit/add/remove
  - Shows per‑section status: Saving… → Saved at HH:MM:SS or Error at HH:MM:SS
  - Updates global footer with "Last saved at HH:MM:SS" on success

### Field Help Tooltips
- Added `help_text` column to `CustomFormField` for contextual help
- Edit Field form now includes a Help Text textarea
- YAML template import supports `help` or `help_text` keys
- Tooltips render as an info icon next to labels on data entry

### Ordering & Grouping
- Stable ordering in routes when fetching fields:
  - Ordered by `section`, then `sort_order` (fallback to `id`)

### Backend Changes
- New route in `app/routes.py`:
  - `autosave_study_data` handles per‑section and numerical outcomes autosave
- Existing `enter_data` route updated to return fields in stable order

### Database Migrations
- Added migration: `9f2b3c1a5add_add_help_text_to_custom_form_field.py`
  - Adds `help_text` to `custom_form_field`
- Migration chain fix:
  - Resolved multiple heads by setting `down_revision = '3a6f1e2b9cde'` for help_text migration
- Related prior migration: `3a6f1e2b9cde_add_sort_order_to_custom_form_field.py`

### Files Updated
- `app/routes.py`
- `app/models.py`
- `app/forms.py`
- `app/utils.py`
- `app/templates/base.html`
- `app/templates/index.html`
- `app/templates/project_detail.html`
- `app/templates/form_fields.html`
- `app/templates/enter_data.html`
- `migrations/versions/9f2b3c1a5add_add_help_text_to_custom_form_field.py`

## Notes
- Tooltips: populate by editing a field in Customize Form and setting Help text
- Autosave: requires CSRF token (added via meta tag in base layout)
- Migration: run `flask db upgrade` if not already applied

