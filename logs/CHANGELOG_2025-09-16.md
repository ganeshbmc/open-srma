# Changelog — 2025-09-16

## Summary
Implemented Study ID autofill with RBAC enforcement, surfaced Study ID on the project’s study list, fixed a return-path bug in the project page, added an Author field hint, and introduced a lightweight workflow to fetch GitHub Project (v2) board items via a script and Make target (with pagination and status normalization).

## Details

### Data Entry & RBAC
- Study ID autofill
  - Auto-fills as "Author et al, Year" on the data entry page when empty.
  - Owners/Admins can edit; Members see read-only.
  - Enforcement on both full save and autosave: member edits are ignored server-side; defaults backfilled if empty.
- Template support
  - The Study ID field is detected by label "Study ID" with type `text` from form templates (RCT v1/v2).

### Project Page (Studies list)
- Shows stored Study ID under each study when available; falls back to "Author, Year".
- Fixed a 500 error regression in `project_detail` by ensuring the template render is returned outside of the `except` block.

### UX Tweaks
- Add Study form: Author field now shows a helper hint and placeholder (standard is first author’s last name).

### GitHub Projects (v2) Integration
- Added a small script and Make target to list board items by Status (“Todo”, “In Progress”).
- Handles GraphQL pagination (100 per page) and normalizes status text ("To Do" ↔ "Todo").
- Docs include token setup (read-only) and usage examples.

### Developer Experience
- Makefile target `project-list` sources `.env` and runs the script, e.g.:
  - `make project-list STATUS="In Progress"`
  - `make project-list STATUS="Todo"`

## Files Updated / Added
- Updated
  - `app/routes.py`
    - Added Study ID autofill defaults and RBAC enforcement on save/autosave.
    - Project page now resolves and displays Study ID for studies.
    - Fixed missing `return` after `except` in `project_detail`.
  - `app/templates/enter_data.html`
    - Renders Study ID as read-only for Members; shows explanatory hint.
  - `app/templates/project_detail.html`
    - Displays Study ID (when present) instead of "Author, Year".
  - `app/templates/add_study.html`
    - Adds placeholder and hint for Author field.
  - `Makefile`
    - New `project-list` target; help text updated.
  - `docs/GITHUB_PROJECTS_WORKFLOW.md`
    - Board workflow, token scopes, usage; references “Todo” column.
- Added
  - `scripts/fetch_project_items.py`
    - GraphQL fetch for user Project v2 items by Status; supports pagination and optional PRs.

## Notes
- Study ID detection relies on a field labeled exactly "Study ID" (case-insensitive) in the project’s form.
- Ensure `.env` contains `GH_TOKEN` with Projects (v2) read access to use the board fetch script.
- Members can still view Study ID; only Owners/Admins can edit it.
