# YC Monitor — U.S. Treasury Yield Curve Pipeline

A personal data engineering project that tracks the U.S. Treasury yield curve daily.
Data is pulled automatically from the Federal Reserve (FRED), stored in AWS S3,
transformed with dbt, and served as a live static dashboard updated via GitHub Actions.

**Live dashboard:** https://alexanderdevano.github.io/yield-curve-pipeline/

---

## Architecture

```
FRED API -> AWS Lambda -> S3 -> dbt (Athena) -> GitHub Actions -> GitHub Pages
```

Lambda runs on a daily schedule via EventBridge. Raw data lands in S3 as Parquet.
dbt runs transformations in Athena for data quality and analysis. GitHub Actions
reads the raw Parquet directly from S3, generates a static HTML dashboard, and
deploys it to GitHub Pages daily.

---

## Stack

| Layer | Tool |
|-------|------|
| Ingestion | Python, FRED API |
| Storage | AWS S3 (Parquet) |
| Automation | AWS Lambda, EventBridge |
| Transformation | dbt, AWS Athena |
| CI/CD | GitHub Actions |
| Dashboard | HTML, Chart.js, GitHub Pages |

---

## Data

Daily U.S. Treasury yields from 2000 to present across six maturities:
3 Month, 1 Year, 2 Year, 5 Year, 10 Year, 30 Year.

Recession periods from NBER via FRED series USREC.

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
│   └── fetch_fred.py           # pulls FRED data, uploads to S3
├── infrastructure/
│   └── lambda_handler.py       # AWS Lambda entry point
├── yield_curve_dbt/
│   └── models/
│       ├── staging/            # cleans raw data
│       └── marts/              # computes spreads and inversion flags
├── dashboard/
│   └── generate_dashboard.py   # reads S3, computes metrics, generates index.html
└── .github/
    └── workflows/
        └── update_dashboard.yml  # daily CI/CD to regenerate and deploy dashboard
```

---

## How It Works

1. **Lambda** pulls fresh yield data from FRED daily at 7AM UTC and stores it in S3 as Parquet
2. **dbt** runs transformation models in Athena for data quality testing and analysis
3. **GitHub Actions** runs at 8AM UTC, reads the latest Parquet from S3, computes spreads
   and inversion flags in pandas, generates a static HTML dashboard, and pushes to GitHub Pages
4. **GitHub Pages** serves the updated dashboard at the live URL above

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

# add credentials to .env
echo "FRED_API_KEY=your_key_here" >> .env

# pull data and generate dashboard
python ingestion/fetch_fred.py
python dashboard/generate_dashboard.py
open dashboard/index.html
```

---

## Author

Alexander Devano Aryasena, 2026
