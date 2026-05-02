import requests
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import date
from dotenv import load_dotenv
import os
import boto3
import io

load_dotenv()
API_KEY = os.getenv("FRED_API_KEY")
BUCKET = "yield-curve-pipeline"

SERIES = {
    "DGS3MO": "3_month",
    "DGS1":   "1_year",
    "DGS2":   "2_year",
    "DGS5":   "5_year",
    "DGS10":  "10_year",
    "DGS30":  "30_year"
}

def fetch_series(series_id, label):
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id, 
        "api_key": API_KEY,
        "file_type": "json",
        "observation_start": "2000-01-01"
    }

    r = requests.get(url, params=params)
    r.raise_for_status()

    observations = r.json()['observations']
    df = pd.DataFrame(observations)[['date', 'value']]
    df['maturity'] = label
    df['series_id'] = series_id

    return df

def upload_to_s3(df, bucket, key):
    buffer = io.BytesIO()
    pq.write_table(pa.Table.from_pandas(df), buffer)
    buffer.seek(0)

    s3 = boto3.client("s3", region_name="ap-southeast-2")
    s3.put_object(Bucket=bucket, Key=key, Body=buffer.getvalue())
    print(f"uploaded to s3://{bucket}/{key}")

def main():
    all_dfs = []

    for series_id, label in SERIES.items():
        print(f'pulling {label} ...')
        df = fetch_series(series_id, label)
        all_dfs.append(df)

    combined = pd.concat(all_dfs, ignore_index=True)

    # FRED uses "." when data is missing, convert those to NaN
    combined["value"] = pd.to_numeric(combined["value"], errors='coerce')

    # track when I pulled this so I can detect stale data later
    combined["pulled_at"] = date.today().isoformat()

    # save locally only if running on local machine
    local_path = f"data/raw/yield_curve_{date.today()}.parquet"
    if os.path.exists("data/raw/"):
        pq.write_table(pa.Table.from_pandas(combined), local_path)
        print(f"saved locally to {local_path}")
    else:
        print("running in Lambda")


    # upload to s3
    s3_key = f"raw/yield_curve_{date.today()}.parquet"
    upload_to_s3(combined, BUCKET, s3_key)

if __name__ == "__main__":
    main()


