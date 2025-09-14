# open-srma

**open-srma** is an open-source platform for **systematic reviews and meta-analysis (SRMA)**.  
It supports the SRMA workflow — from **data extraction** to **narrative synthesis** and **quantitative meta-analysis** — in a transparent and reproducible way.

See the high-level overview: [Project Summary](project_summary.md).

For upcoming roadmap tasks, see: [Next Steps](next_steps.md).

For authentication, roles, and permissions, see: [RBAC Rules and Workflow](RBAC_info.md).

### ✨ Features
- 📑 Structured web-based forms for data extraction (multi-user, double entry & reconciliation)
- 📝 Narrative synthesis support (study characteristics, risk of bias, qualitative summaries)
- 📊 Built-in integration with R (`meta`, `metafor`) for forest plots, funnel plots, and advanced analyses
- 🔄 Flexible outputs:
  - Standardized CSV/JSON exports
  - Project-wide static field export to CSV
  - Compatible with RevMan, JASP, MetaXL, CMA
  - Seamless use in custom R or Python pipelines
- 📈 One-click HTML/PDF reports with forest/funnel plots and model summaries
- 🔐 Audit trails and version control for transparent review workflows

### 🏗️ Project Structure
The project is divided into two main parts:

1.  **Part 1: Data Extraction & Export**
    *   Build a web application with custom forms for SRMA projects.
    *   Human experts use these forms to extract data from studies.
    *   Save the extracted data to a database.
    *   Export the data to CSV/Excel formats compatible with downstream meta-analysis software (e.g., MetaXL, JASP, RevMan, JAMOVI).

2.  **Part 2: Integrated Meta-Analysis**
    *   Develop custom meta-analysis pipelines using R and/or Python.
    *   Allow users to perform analysis directly within the platform.

### 🔧 Tech stack
- **Python (Flask, Pandas, SQLAlchemy)** — web app, data handling, and API
- **R (meta, metafor, rmarkdown/quarto)** — analysis and reporting
- **Docker** — optional containerized deployment for reproducibility

### 🚀 Running (Dev & Prod)
- Environment variables
  - `FLASK_APP=run.py` (Flask CLI context)
  - `FLASK_ENV` (`development` for local dev) or `FLASK_DEBUG=1` to enable debug
  - `HOST` (default `0.0.0.0`) and `PORT` (default `5000`)
  - `SECRET_KEY` (set a strong value in production)
- Development
  - Python entrypoint: `FLASK_DEBUG=1 python run.py`
  - Or Flask CLI: `export FLASK_APP=run.py && export FLASK_ENV=development && flask run --host=0.0.0.0 --port=5000`
- Production
  - The app binds to `0.0.0.0:${PORT}` and runs without debug when `FLASK_ENV`/`FLASK_DEBUG` are unset.
  - Run DB migrations on start: `flask db upgrade` (requires `FLASK_APP=run.py`).
  - Example WSGI command: `gunicorn -w 2 -k gthread -b 0.0.0.0:${PORT} wsgi:app`.
  - For SQLite persistence, mount a volume at `/app/instance`.

### 📜 License
[MIT License](LICENSE) – free to use, modify, and share.

### 🧪 Demo Accounts (for local development)
If you run `make seed`, the script creates demo users and a sample project:
- Owner (admin): `owner@example.com` / `demo123`
- Member: `member@example.com` / `demo123`

These credentials are intended for local development only. The seed script also prints them after seeding. Remove demo data with `make seed-clean`.
