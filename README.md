# open-srma

**open-srma** is an open-source platform for **systematic reviews and meta-analysis (SRMA)**.  
It supports the full workflow — from **data extraction** to **narrative synthesis** and **quantitative meta-analysis** — in a transparent and reproducible way.

### ✨ Features
- 📑 Structured web-based forms for data extraction (multi-user, double entry & reconciliation)
- 📝 Narrative synthesis support (study characteristics, risk of bias, qualitative summaries)
- 📊 Built-in integration with R (`meta`, `metafor`) for forest plots, funnel plots, and advanced analyses
- 🔄 Flexible outputs:
  - Standardized CSV/JSON exports
  - Compatible with RevMan, JASP, MetaXL, CMA
  - Seamless use in custom R or Python pipelines
- 📈 One-click HTML/PDF reports with forest/funnel plots and model summaries
- 🔐 Audit trails and version control for transparent review workflows

### 🔧 Tech stack
- **Python (Flask, Pandas, SQLAlchemy)** — web app, data handling, and API
- **R (meta, metafor, rmarkdown/quarto)** — analysis and reporting
- **Docker** — optional containerized deployment for reproducibility

### 📜 License
[MIT License](LICENSE) – free to use, modify, and share.
