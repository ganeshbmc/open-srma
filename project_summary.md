# Project Summary

- Open-source platform for systematic reviews and meta-analysis.
- Starts with structured data extraction from RCT PDFs (one intervention vs one control).
- End-to-end workflow: extraction → narrative synthesis → meta-analysis.
- Outputs clean CSV/Excel, plots, and reports; compatible with external tools or R/Python pipelines.

## Architecture

- Part 1: Data Extraction & Export — web forms, database storage, clean exports for external analysis.
- Part 2: Integrated Meta-Analysis — in-app R/Python pipelines for analyses, plots, and reporting.

## Tech Stack

- Backend: Python (Flask, Pandas, SQLAlchemy)
- Database: SQLite initially; expandable to Postgres/MySQL
- Analysis/Plots: R (meta, metafor)
- Deployment: Docker
- Frontend (optional): Vue for richer interactions (repopulation, autosave)

## CLI Agent Role

- Developer-side assistant (not user-facing).
- Manages environment, database, and data exports.
- Runs analysis jobs and generates outputs.
- Assists with packaging/testing, including Docker builds.
- Supports iterative development and reproducibility.

## Roadmap

- Future support for multi-arm RCTs, observational designs, and risk of bias modules.

