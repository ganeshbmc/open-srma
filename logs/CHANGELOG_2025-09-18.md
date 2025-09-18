# Changelog — 2025-09-18

## Summary
Improved password reset robustness (email support + resilience) and hardened project setup/delete flows with better confirmations and validation.

## Details

### Password Reset
- Added optional SMTP configuration via env vars (`MAIL_*`), helper to send reset emails, and UI tweaks to hide dev links when mail sends succeed.
- Forgot password now logs and surfaces fallback links instead of 500s when SMTP is unreachable (e.g., restricted Railway plans).

### Project & Study Management
- Added cancel/back buttons for project creation/detail pages; surfaced project `created_at` dates.
- Added study deletion controls with owner-only enforcement plus member request workflow and confirmations.
- Introduced remove-member confirmation, disallow removing the final owner.
- Added confirmation prompts for removing outcomes (form & study data) and baseline rows.

### Template & YAML Workflow
- Removed duplicate “Not reported” option from sample size estimation dropdown.
- Enforced YAML validation during custom form setup: empty/non-UTF8 files and schema issues now flash descriptive errors without corrupting state.

### Auth Improvements
- Implemented forgot-password UI screens and login link; tokens stored in new `password_reset_token` table.

## Migrations
- `a5f0c1b2d3e4_add_created_at_to_project.py`
- `b6d7e8f90123_add_password_reset_token.py`

## Tests / Checks
- `venv/bin/python -m compileall app`
- `make migrate`

