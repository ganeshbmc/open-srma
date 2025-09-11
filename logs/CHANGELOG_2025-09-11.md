# Changelog — 2025-09-11

## Summary
This session adds robust export features (CSV/Excel and zipped per‑outcome files for both dichotomous and continuous outcomes), richer baseline data entry, project‑level outcome presets, a safer project deletion workflow, and a more flexible setup flow for creating data extraction forms.

## Details

### Breaking Changes
- Login required for all project/study routes (RBAC introduced).
- Excel static export removed; static export is now CSV-only.
- Outcomes export route renamed to `export_outcomes` (old `export_jamovi` kept as alias).

### Exports
- New static fields export for a project:
  - Route: `GET /project/<id>/export_static?format=csv|xlsx`.
  - Buttons added on Project page for CSV and Excel.
  - Updated: Excel export removed; static export is CSV-only and grouped under a single Export dropdown.
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
  - `fea12db89a10_add_options_to_custom_form_field.py` (select/dropdown support)

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

### RCT Template Refinement
- Updated `app/form_templates/rct_v1.yaml` to model baseline characteristics per arm:
  - Moved `Age` from Participants to Patient Baseline Characteristics and changed to `baseline_continuous` (mean/SD per arm).
  - Added `Female (%)` as `baseline_categorical` (percent per arm).
  - Added common baseline continuous fields such as `BMI` and a generic `Baseline severity/score` as `baseline_continuous`.
- App already supports these types in data entry and exports; no code changes required beyond YAML import (help texts are stored).

### RCT Template v2 (Dropdowns and NR)
- Added `app/form_templates/rct_v2.yaml` with dropdown/select support and NR (not reported) options:
  - `Assessor` uses `select_member` to pick from project owners/members (plus NR).
  - `Randomization type` and multiple blinding fields use `select` with preset choices and optional NR.
- Model changes: `CustomFormField.options` (JSON) stores select choices and configuration.
- Loader: `load_template_and_create_form_fields` now reads `options` from YAML and persists it.
- Enter Data UI: renders `select` and `select_member` fields; `select_member` choices are built from project memberships; all include an NR choice.
- Setup Form: default template changed to `rct_v2` (legacy `rct_v1` still available).
- Setup Form now supports uploading a custom YAML template and downloading bundled templates (`rct_v1.yaml`, `rct_v2.yaml`) for reference.
 - Added strict YAML validation for templates: verifies section/field structure, supported field types, and `options` schema for `select`/`select_member` fields with clear error messages on failure.

### Seeding (Demo Data)
- `make seed` now creates demo users and memberships for RBAC testing:
  - Owner (admin): `owner@example.com` / `demo123`
  - Member: `member@example.com` / `demo123`
  - Adds both as project memberships to the "Demo SRMA" project; sets `Study.created_by` to the owner.
- `make seed-clean` also removes project memberships while retaining user accounts.

---

## RBAC and Access Control (2025-09-11)

### Dependencies
- Added `Flask-Login==0.6.3` to requirements.

### Models & Migrations
- New models:
  - `User`: accounts with `email`, `name`, `password_hash`, `is_admin`, `is_active`, timestamps.
  - `ProjectMembership`: links users to projects with `role` (`owner`|`member`) and unique `(user_id, project_id)`.
  - `FormChangeRequest`: queued member proposals for form/outcome changes with status workflow.
- Updated models:
  - `Study.created_by` (nullable FK to `user.id`).
  - `Project.memberships` relationship added.
- Migration added: `e3a1b9c7a001_add_rbac_models.py` (follows `c1de23a4b567`).
  - Fix: set `down_revision` to `c1de23a4b567` to avoid multiple heads.

### Auth & RBAC Helpers
- Initialized `LoginManager` and `user_loader` in `app/__init__.py`.
- Helpers in routes: `is_admin()`, `get_membership_for()`, `require_project_member()`, `require_project_owner()`.
- Index (`/`) now requires login; shows projects by membership (admins see all).
- Creating a project makes the creator an Owner via a membership row.

### Routes (Auth, Membership, Requests)
- Auth:
  - `GET/POST /register` (register new user)
  - `GET/POST /login` (login)
  - `POST /logout`
- Membership management (Owner/Admin):
  - `GET/POST /project/<id>/members` (add existing users by email; set role owner/member)
- Change requests (Owner/Admin):
  - `GET /project/<id>/requests` (list)
  - `POST /project/<id>/requests/<req_id>/approve|reject`
  - Resolved requests now hide action buttons (UI shows a "Resolved" badge).

### Form/Outcome Change Proposals
- Members proposing add/edit/delete field, move up/down, add/delete outcome now create `FormChangeRequest` instead of applying immediately.
- Owners/Admins still apply changes immediately.
- Approval application implemented for: `add_field`, `edit_field`, `delete_field`, `add_outcome`, `delete_outcome`.
- Reorder (`reorder_field`, `reorder_section`) is captured but not auto‑applied yet (owner can reorder directly). Future work: apply on approve.
 - Members can include a reason when proposing: add/edit/delete field, add/delete outcome, and reorder field/section. Reasons are displayed to owners on the Requests page.

### Route Guards
- Project pages, enter data, exports: require membership.
- Setup/customize form, manage members, approve requests, delete project: Owner/Admin only.

### CLI Helpers
- New Flask CLI commands (documented in `make_commands.md`):
  - `flask create-user [--admin]`
  - `flask promote-admin <email>`
  - `flask add-membership <email> <project_id> <owner|member>`
- Implemented in `app/cli.py` and registered in app init.

### UI Updates
- Navbar shows Login/Register or Logout + user name.
- New pages: `auth_login.html`, `auth_register.html`, `members.html`, `requests.html`.
- Role badges (Admin/Owner/Member) surfaced on:
  - Project list, Project detail, Customize Form, and Enter Data pages.
- Pending requests badges on Project detail and Customize Form.
 - Project detail export actions consolidated into an "Export" dropdown; Excel option removed.

### Exports (Naming/Routes)
- Outcomes export endpoint renamed to `export_outcomes`; kept `export_jamovi` as a backward‑compatible alias.
- Internal variable names standardized (`outcome_columns`).

### Enter Data: RBAC Enforcement & UX
- Members cannot add free‑form outcome rows; they can only insert predefined outcomes (owners/admins retain full controls).
- Server‑side enforcement for members: only predefined outcome names are accepted for saves/autosaves.
- Bugfix: Saving outcomes as a member no longer deletes unrelated existing outcomes. We now upsert per outcome name for members (delete/replace only the submitted predefined names); owners/admins still replace all rows.
- Prevented unintended form submissions/scroll jumps by canceling default actions on outcome add/save buttons.

### Documentation
- Added `RBAC_info.md` detailing roles, permissions, workflows, and payload shapes.
- Linked from `README.md`, `next_steps.md`, `DESIGN_AND_PLAN.md`, `AGENTS.md`, and `make_commands.md`.
