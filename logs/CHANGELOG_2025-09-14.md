# Changelog — 2025-09-14

## Summary
Production‑ready deployment setup, Postgres support, and Railway configuration were added. The app now runs behind gunicorn, picks DB settings from environment variables, exposes a health endpoint, and ships with a Procfile for Railway. Migrations were fixed for Postgres defaults.

## Details

### Deployment & Runtime
- Added gunicorn start via Procfile with safe defaults for SQLite and Postgres.
- `run.py` now reads `HOST`, `PORT`, and toggles debug via `FLASK_DEBUG`/`FLASK_ENV`.
- Added `wsgi.py` exposing `app` for WSGI servers (gunicorn/uwsgi).
- Added `/healthz` endpoint to report DB backend (`sqlite`/`postgresql`) and connectivity.

### Database & Configuration
- App prefers `DATABASE_URL` (or `RAILWAY_DATABASE_URL`, `POSTGRES_URL`), falls back to constructing from `PGHOST`/`PGUSER`/`PGPASSWORD`/`PGDATABASE`/`PGPORT`; otherwise uses SQLite at `instance/srma.db`.
- Normalizes `postgres://` → `postgresql://` for SQLAlchemy.
- SQLite hardening for threaded servers: `check_same_thread=False`, and PRAGMAs `journal_mode=WAL` and `synchronous=NORMAL` on connect.
- `SECRET_KEY` now read from environment with a development fallback.

### Migrations (Postgres compatibility)
- Fixed RBAC migration defaults for Postgres:
  - Boolean defaults changed from `0/1` to `false/true`.
  - `created_at` defaults changed to `CURRENT_TIMESTAMP` (removed parentheses).

### Tooling & DX
- `requirements.txt`: added `gunicorn` and `psycopg2-binary`.
- Makefile improvements:
  - `make run` enables debug via `FLASK_DEBUG=1`.
  - `.env` auto‑loaded for `run`, `run-prod`, `migrate`, `seed`, `seed-clean`.
  - New `run-prod` target: applies migrations then starts gunicorn on `:8000`.
- Docs:
  - README: added Dev/Prod run instructions, `.env` quick start, Railway deployment guide, Postgres notes.
  - `make_commands.md`: updated to reflect new Make targets and `.env` behavior.
  - Added `.env.example`; `.env` ignored via `.gitignore`.

## Files Updated
- `run.py`
- `wsgi.py` (new)
- `app/__init__.py`
- `app/routes.py` (added `/healthz`)
- `requirements.txt`
- `Procfile` (new)
- `Makefile`
- `make_commands.md`
- `README.md`
- `migrations/versions/e3a1b9c7a001_add_rbac_models.py`
- `.env.example` (new)
- `.gitignore`

## Notes
- Railway
  - Set `SECRET_KEY` and `DATABASE_URL` on the web service (can reference `${{ Postgres.DATABASE_URL }}`), then redeploy.
  - Verify `/healthz` returns `"db_backend": "postgresql"` and `"db_ok": true`.
  - For SQLite persistence instead of Postgres, attach a Volume mounted at `/app/instance` and keep single gunicorn worker.
- Scaling
  - On Postgres, you may increase gunicorn workers (e.g., `-w 2`) once confirmed stable.
- Local
  - Copy `.env.example` to `.env` for convenient local config; use `make run` (dev) or `make run-prod` (prod‑like).
