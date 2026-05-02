# YC Monitor — U.S. Treasury Yield Curve Pipeline

A personal data engineering project that tracks the U.S. Treasury yield curve daily.
Data is pulled automatically from the Federal Reserve (FRED), stored in AWS S3,
transformed with dbt, and served as a static dashboard.

**Live dashboard:** https://alexanderdevano.github.io/yield-curve-pipeline/

---

## Architecture

```
FRED API -> AWS Lambda -> S3 -> AWS Athena -> dbt -> HTML Dashboard
```

Lambda runs on a daily schedule via EventBridge. Raw data lands in S3 as Parquet,
dbt computes spreads and inversion flags in Athena, and the dashboard is generated
as a static HTML file served via GitHub Pages.

---

## Stack

| Layer | Tool |
|-------|------|
| Ingestion | Python, FRED API |
| Storage | AWS S3 (Parquet) |
| Automation | AWS Lambda, EventBridge |
| Query layer | AWS Athena |
| Transformation | dbt |
| Dashboard | HTML, Chart.js, GitHub Pages |

---

## Data

Daily U.S. Treasury yields from 2000 to present across six maturities:
3 Month, 1 Year, 2 Year, 5 Year, 10 Year, 30 Year.

Source: Federal Reserve Economic Data (FRED), St. Louis Fed.

---

## Business Questions

- Is the yield curve currently inverted?
- How deep is the inversion and how long has it lasted?
- How does today compare to previous inversion cycles?
- When did past inversions occur and what followed?

---

## Project Structure

```
yield_curve_pipeline/
├── ingestion/
│   └── fetch_fred.py          # pulls FRED data, uploads to S3
├── infrastructure/
│   └── lambda_handler.py      # AWS Lambda entry point
├── yield_curve_dbt/
│   └── models/
│       ├── staging/           # cleans raw data
│       └── marts/             # computes spreads and inversion flags
└── dashboard/
    └── generate_dashboard.py  # generates index.html from Athena data
```

---

## Running Locally

```bash
# clone the repo
git clone https://github.com/alexanderdevano/yield-curve-pipeline.git
cd yield-curve-pipeline

# set up environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# add your FRED API key to .env
echo "FRED_API_KEY=your_key_here" >> .env

# pull data and generate dashboard
python ingestion/fetch_fred.py
python dashboard/generate_dashboard.py
open dashboard/index.html
```

---

## Author

Alexander Devano Aryasena, 2026
