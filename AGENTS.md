# AGENTS.md

## Project Overview
`open-srma` is an open-source platform for **systematic reviews and meta-analysis**.  
The initial focus is on **structured data extraction** from PDFs of randomized controlled trials (one intervention vs one control).  
The workflow spans from **data extraction** to **narrative synthesis** and **meta-analysis**, with flexible outputs (CSV/Excel, plots, reports) compatible with other meta-analysis software or custom R/Python pipelines.  
Future expansions may include multi-arm RCTs, observational designs, and risk of bias modules.

## Project Structure
The project is divided into two main parts:

1.  **Part 1: Data Extraction & Export**
    *   Focuses on building the core application for structured data entry.
    *   Human experts use web forms to extract data, which is saved to a database.
    *   The primary output is clean, exportable data (CSV/Excel) for use in external meta-analysis software.

2.  **Part 2: Integrated Meta-Analysis**
    *   Focuses on building custom meta-analysis pipelines within the application.
    *   Uses R/Python to perform analyses and generate plots/reports directly.

## Tech Stack
- **Python (Flask, Pandas, SQLAlchemy)** — web app, data handling, storage
- **SQLite** (initially; expandable to Postgres/MySQL) — data persistence
- **R (`meta`, `metafor`)** — statistical analysis, forest/funnel plots, reports
- **Docker** — deployment after local development and testing
- **Optional Vue** — richer front-end interactions (form repopulation, autosave)

## Role of the CLI Agent
The **CLI agent** is a developer-side assistant.  
Its role is to:
- Help manage the environment, database, and exports.
- Run analysis jobs and generate outputs.
- Assist in packaging and testing (e.g., Docker builds).
- Act as a lightweight programmer alongside the maintainer, supporting iterative development and roadmap execution.

The CLI agent does **not** form part of the end-user product experience. It is a tool to make development smoother and more reproducible.

