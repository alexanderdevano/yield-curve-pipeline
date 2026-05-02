# Yield Curve Pipeline

An automated data engineering pipeline that tracks the U.S. Treasury yield curve daily.

## Architecture

FRED API → AWS Lambda → S3 → AWS Athena → dbt → Streamlit

## Stackgi

- **Ingestion**: Python, FRED API
- **Storage**: AWS S3 (Parquet format)
- **Automation**: AWS Lambda + EventBridge (daily schedule)
- **Query Layer**: AWS Athena
- **Transformation**: dbt
- **Dashboard**: Streamlit (coming soon)

## Data

Daily U.S. Treasury yields from 2000 to present:
- 3 Month, 1 Year, 2 Year, 5 Year, 10 Year, 30 Year

## Business Questions

- Is the yield curve currently inverted?
- How long has it been inverted?
- How does today's curve compare to 2008 or 2020?