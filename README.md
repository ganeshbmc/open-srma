# open-srma

**open-srma** is an open-source platform for **systematic reviews and meta-analysis (SRMA)**.  
It supports the SRMA workflow — from **data extraction** to **narrative synthesis** and **quantitative meta-analysis** — in a transparent and reproducible way.

See the high-level overview: [Project Summary](project_summary.md).

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

### 📜 License
[MIT License](LICENSE) – free to use, modify, and share.
