# Changelog — 2025-09-17

## Summary
Introduced comprehensive validation across the auth flow and data-entry stack: stronger registration/login rules, stricter project/study creation constraints, rich inline feedback for researchers capturing study data (including "Other (specify)" handling), and hardened autosave/server persistence checks.

## Details

### Authentication
- Registration
  - Enforces sanitized name/email input with stricter character limits.
  - Adds password strength checks (length, letter+number, no leading/trailing whitespace).
  - Surfaces duplicate-email errors inline instead of flashing a generic message.
- Login
  - Normalizes email input, propagates invalid credential / inactive account errors beside the relevant field for better UX.
  - Switches to `EmailField`/`PasswordField` for semantic HTML5 validation.

### Project & Study Creation
- Adds trim/length validators to project names, study titles/authors.
- Requires study year to fall within 1800–2100; exposes invalid entries next to the field for quick correction.
- Updates the add-project and add-study templates to display validation errors inline.

### Data Entry (Static Fields)
- Uniformly trims/sanitizes user input before saving.
- Adds per-field validators for text, textarea, integer (>=0), date (ISO format), select, select_member, dichotomous outcomes, baseline continuous/categorical blocks.
- Flags missing or malformed entries directly beneath the offending control and keeps user-entered values on error.
- Required fields now mark `required` in the DOM for browser assistance.

### "Other (specify)" Workflow
- Dropdowns exposing "Other (specify)" show a companion textbox automatically when selected.
- Textbox requirement mirrors backend validation; clearing/switching options hides the textbox and clears stray input.
- Autosave payloads carry both selected value and custom text so partial edits are preserved.

### Autosave & Server Persistence
- Shared `_process_field_input` routine ensures consistent validation across full submit and autosave paths.
- Back-end rejects invalid autosave payloads with descriptive errors (e.g., unauthorized outcome names, malformed numbers) before touching the database.
- Preserves existing Study ID enforcement (members still read-only, defaults reapplied if absent).


### Form Cleanup from Project Board (Issues #14, #15, #16, #17, #18, #19, #20, #21, #24)
- Removed assessor NR option and limited choices to project members/owners (#14).
- Dropped obsolete fields: ethical approval, method of recruitment, withdrawals/exclusions (#17, #20).
- Added a "General Comments" section positioned after funding with helper text (#18).
- Split "No. missing" into intervention/control fields and validated input (#21).
- Updated Study Identification labels and hints: `Reference citation` → `DOI` with format guidance; population/setting fields now include example text (#19, #24).
- Converted key text fields to curated dropdowns (study design, unit of allocation, sample size estimation, randomization type) with "Other (specify)" support (#15, #16, #21).

### Files Updated
- `app/forms.py`
- `app/routes.py`
- `app/templates/auth_register.html`
- `app/templates/auth_login.html`
- `app/templates/add_project.html`
- `app/templates/add_study.html`
- `app/templates/enter_data.html`

## Tests
- `source .envrc && venv/bin/python -m compileall app`
