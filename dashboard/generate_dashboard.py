"""
generate_dashboard.py
Pulls data from Athena and generates dashboard/index.html
Usage: python generate_dashboard.py

Author: Alexander Devano Aryasena
Built: 2026
Stack: Python, AWS (Lambda, S3, Athena), dbt, FRED API
"""

import json
from datetime import datetime

try:
    import pandas as pd
    from pyathena import connect

    conn = connect(
        s3_staging_dir="s3://yield-curve-athena-results/",
        region_name="ap-southeast-2"
    )

    spreads = pd.read_sql(
        "SELECT * FROM yield_curve.yield_spreads ORDER BY date",
        conn
    )
    inversion = pd.read_sql(
        "SELECT * FROM yield_curve.inversion_flags ORDER BY date",
        conn
    )

    spreads['date'] = pd.to_datetime(spreads['date']).dt.strftime('%Y-%m-%d')
    inversion['date'] = pd.to_datetime(inversion['date']).dt.strftime('%Y-%m-%d')

    latest = spreads.iloc[-1]
    is_inverted = float(latest['spread_10y_2y']) < 0

    dates = spreads['date'].tolist()
    spread_data = spreads['spread_10y_2y'].round(3).tolist()
    inversion_flags = [bool(v) for v in inversion['is_inverted_2y'].tolist()]

    maturities = ["3M", "1Y", "2Y", "5Y", "10Y", "30Y"]
    current_yields = [
        round(float(latest['yield_3m']), 2),
        round(float(latest['yield_1y']), 2),
        round(float(latest['yield_2y']), 2),
        round(float(latest['yield_5y']), 2),
        round(float(latest['yield_10y']), 2),
        round(float(latest['yield_30y']), 2),
    ]

    all_yields = {}
    for _, row in spreads.iterrows():
        try:
            all_yields[row['date']] = [
                round(float(row['yield_3m']), 2),
                round(float(row['yield_1y']), 2),
                round(float(row['yield_2y']), 2),
                round(float(row['yield_5y']), 2),
                round(float(row['yield_10y']), 2),
                round(float(row['yield_30y']), 2),
            ]
        except:
            pass

    data_date = latest['date']
    yield_10y = round(float(latest['yield_10y']), 2)
    yield_2y = round(float(latest['yield_2y']), 2)
    yield_3m = round(float(latest['yield_3m']), 2)
    spread_value = round(float(latest['spread_10y_2y']), 2)

    inv_df = inversion[inversion['is_inverted_2y'] == True].copy()
    inv_df['date'] = pd.to_datetime(inv_df['date'])
    inv_df['period'] = (inv_df['date'].diff().dt.days > 5).cumsum()
    periods = inv_df.groupby('period').agg(
        start=('date', 'min'),
        end=('date', 'max'),
        days=('date', 'count'),
        min_spread=('spread_10y_2y', 'min')
    ).reset_index(drop=True)
    periods['start'] = periods['start'].dt.strftime('%Y-%m-%d')
    periods['end'] = periods['end'].dt.strftime('%Y-%m-%d')
    periods['min_spread'] = periods['min_spread'].round(2)
    inversion_periods = periods.to_dict('records')

    total_days = len(inversion)
    total_inverted = int(inversion['is_inverted_2y'].sum())
    pct_inverted = round((total_inverted / total_days) * 100, 1)

    print(f"Data loaded: {len(spreads)} rows, latest: {data_date}")

except Exception as e:
    print(f"Athena connection failed: {e}")
    print("Using sample data...")

    import random
    random.seed(42)

    data_date = "2026-04-30"
    yield_10y = 4.40
    yield_2y = 3.88
    yield_3m = 3.68
    spread_value = 0.52
    is_inverted = False
    maturities = ["3M", "1Y", "2Y", "5Y", "10Y", "30Y"]
    current_yields = [3.68, 3.72, 3.88, 4.02, 4.40, 4.98]

    base_spreads = {
        2000: 0.5, 2001: 0.2, 2002: 0.8, 2003: 1.2, 2004: 0.9,
        2005: 0.2, 2006: -0.1, 2007: -0.5, 2008: 1.5, 2009: 2.8,
        2010: 2.5, 2011: 2.0, 2012: 1.5, 2013: 2.3, 2014: 1.8,
        2015: 1.5, 2016: 1.2, 2017: 0.8, 2018: 0.2, 2019: -0.1,
        2020: 0.5, 2021: 0.8, 2022: -0.5, 2023: -1.0, 2024: -0.2,
        2025: 0.3, 2026: 0.52
    }

    dates = []
    spread_data = []
    inversion_flags = []
    all_yields = {}

    for year in range(2000, 2027):
        base = base_spreads.get(year, 0.5)
        for month in range(1, 13):
            if year == 2026 and month > 4:
                break
            date_str = f"{year}-{month:02d}-01"
            spread = round(base + random.uniform(-0.1, 0.1), 3)
            dates.append(date_str)
            spread_data.append(spread)
            inversion_flags.append(spread < 0)
            base_3m = 3.0 + (year - 2000) * 0.05
            all_yields[date_str] = [
                round(base_3m + random.uniform(-0.3, 0.3), 2),
                round(base_3m + 0.1 + random.uniform(-0.2, 0.2), 2),
                round(base_3m + 0.2 + random.uniform(-0.2, 0.2), 2),
                round(base_3m + 0.5 + random.uniform(-0.2, 0.2), 2),
                round(base_3m + spread + 0.2 + random.uniform(-0.1, 0.1), 2),
                round(base_3m + spread + 0.6 + random.uniform(-0.1, 0.1), 2),
            ]

    inversion_periods = [
        {"start": "2006-07-01", "end": "2007-09-01", "days": 292, "min_spread": -0.19},
        {"start": "2019-03-01", "end": "2019-10-01", "days": 161, "min_spread": -0.05},
        {"start": "2022-07-06", "end": "2024-09-17", "days": 563, "min_spread": -1.07},
    ]
    total_days = len(dates)
    total_inverted = sum(1 for f in inversion_flags if f)
    pct_inverted = round((total_inverted / total_days) * 100, 1)


html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>YC Monitor</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@500;600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  :root {{
    --bg: #0c0c0e;
    --surface: #121215;
    --surface2: #1a1a1f;
    --border: rgba(255,255,255,0.06);
    --border2: rgba(255,255,255,0.1);
    --text: #f0f0f4;
    --muted: #76768a;
    --accent: #c9963a;
    --green: #3ecf8e;
    --red: #e05b5b;
    --blue: #6ea8f7;
    --font-display: 'Syne', sans-serif;
    --font-body: 'Inter', sans-serif;
    --font-mono: 'DM Mono', monospace;
  }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: var(--font-body);
    font-size: 14px;
    line-height: 1.6;
    min-height: 100vh;
  }}
  .top-bar {{
    border-bottom: 1px solid var(--border);
    padding: 0 2.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 56px;
    background: var(--surface);
    position: sticky;
    top: 0;
    z-index: 100;
  }}
  .logo {{
    font-family: var(--font-display);
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 0.04em;
    color: var(--accent);
  }}
  .top-bar-right {{
    display: flex;
    align-items: center;
    gap: 1.25rem;
    font-size: 12px;
    color: var(--muted);
    font-family: var(--font-mono);
  }}
  .status-pill {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    font-family: var(--font-body);
  }}
  .status-pill.normal {{ background: rgba(62,207,142,0.1); color: var(--green); border: 1px solid rgba(62,207,142,0.2); }}
  .status-pill.inverted {{ background: rgba(224,91,91,0.1); color: var(--red); border: 1px solid rgba(224,91,91,0.2); }}
  .status-dot {{ width: 5px; height: 5px; border-radius: 50%; background: currentColor; animation: pulse 2s infinite; }}
  @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} }}
  .main {{ max-width: 1300px; margin: 0 auto; padding: 2.5rem; }}
  .page-header {{ margin-bottom: 2.5rem; }}
  .page-title {{
    font-family: var(--font-display);
    font-size: 26px;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 6px;
    letter-spacing: -0.01em;
  }}
  .page-subtitle {{ font-size: 13px; color: var(--muted); }}
  .metrics-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1px;
    background: var(--border);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 1.5rem;
  }}
  .three-col {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1px;
    background: var(--border);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 1.5rem;
  }}
  .metric-card {{ background: var(--surface); padding: 1.5rem; }}
  .metric-label {{
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 10px;
    font-family: var(--font-body);
  }}
  .metric-value {{
    font-size: 30px;
    font-weight: 500;
    color: var(--text);
    font-family: var(--font-mono);
    letter-spacing: -0.03em;
    line-height: 1;
    margin-bottom: 6px;
  }}
  .metric-value.positive {{ color: var(--green); }}
  .metric-value.negative {{ color: var(--red); }}
  .metric-sub {{ font-size: 11px; color: var(--muted); }}
  .alert-bar {{
    padding: 14px 18px;
    border-radius: 8px;
    font-size: 13px;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .alert-bar.normal {{ background: rgba(62,207,142,0.05); border: 1px solid rgba(62,207,142,0.15); color: var(--green); }}
  .alert-bar.inverted {{ background: rgba(224,91,91,0.05); border: 1px solid rgba(224,91,91,0.15); color: var(--red); }}
  .alert-bar span {{ color: var(--text); }}
  .tabs {{ display: flex; border-bottom: 1px solid var(--border); margin-bottom: 1.5rem; }}
  .tab {{
    padding: 10px 18px;
    font-size: 13px;
    color: var(--muted);
    cursor: pointer;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
    transition: color 0.15s, border-color 0.15s;
    user-select: none;
    font-family: var(--font-body);
  }}
  .tab.active {{ color: var(--text); border-bottom-color: var(--accent); }}
  .tab:hover {{ color: var(--text); }}
  .tab-content {{ display: none; }}
  .tab-content.active {{ display: block; }}
  .card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.75rem;
    margin-bottom: 1.5rem;
  }}
  .card-header {{ margin-bottom: 1.5rem; }}
  .card-title {{
    font-family: var(--font-display);
    font-size: 15px;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 4px;
    letter-spacing: -0.01em;
  }}
  .card-subtitle {{ font-size: 12px; color: var(--muted); }}
  .chart-container {{ position: relative; width: 100%; height: 320px; }}
  .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }}
  .insight-box {{
    background: var(--surface2);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 0 8px 8px 0;
    padding: 1rem 1.25rem;
    margin-top: 1.25rem;
    font-size: 12px;
    color: var(--muted);
    line-height: 1.8;
  }}
  .insight-box strong {{ color: var(--text); font-weight: 500; }}
  .date-controls {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem; }}
  .date-label {{
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 6px;
    font-family: var(--font-body);
  }}
  input[type="date"] {{
    width: 100%;
    background: var(--surface2);
    border: 1px solid var(--border2);
    border-radius: 6px;
    padding: 9px 12px;
    color: var(--text);
    font-size: 13px;
    font-family: var(--font-mono);
    outline: none;
    transition: border-color 0.15s;
    color-scheme: dark;
  }}
  input[type="date"]:focus {{ border-color: var(--accent); }}
  .compare-btn {{
    display: inline-flex;
    align-items: center;
    padding: 9px 20px;
    background: var(--accent);
    color: #0c0c0e;
    border: none;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.15s;
    margin-bottom: 1.5rem;
    font-family: var(--font-body);
    letter-spacing: 0.01em;
  }}
  .compare-btn:hover {{ opacity: 0.85; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  thead th {{
    text-align: left;
    padding: 8px 12px;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
    border-bottom: 1px solid var(--border);
    font-family: var(--font-body);
  }}
  tbody tr {{ border-bottom: 1px solid var(--border); transition: background 0.1s; }}
  tbody tr:hover {{ background: var(--surface2); }}
  tbody td {{ padding: 11px 12px; color: var(--text); font-family: var(--font-mono); font-size: 13px; }}
  tbody td.label-col {{ font-family: var(--font-body); color: var(--muted); }}
  tbody td.negative {{ color: var(--red); }}
  .footer {{
    border-top: 1px solid var(--border);
    padding: 1.5rem 2.5rem;
    font-size: 11px;
    color: var(--muted);
    display: flex;
    justify-content: space-between;
    margin-top: 2rem;
    font-family: var(--font-mono);
  }}
</style>
</head>
<body>

<div class="top-bar">
  <span class="logo">YC Monitor</span>
  <div class="top-bar-right">
    <span>{data_date}</span>
    <span class="status-pill {'normal' if not is_inverted else 'inverted'}">
      <span class="status-dot"></span>
      {'Normal' if not is_inverted else 'Inverted'}
    </span>
  </div>
</div>

<main class="main">
  <div class="page-header">
    <h1 class="page-title">U.S. Treasury Yield Curve Monitor</h1>
    <p class="page-subtitle">Daily yield curve analytics. Source: Federal Reserve Economic Data (FRED), St. Louis Fed.</p>
  </div>

  <div class="metrics-grid">
    <div class="metric-card">
      <div class="metric-label">10Y Yield</div>
      <div class="metric-value">{yield_10y:.2f}%</div>
      <div class="metric-sub">10-Year Constant Maturity</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">2Y Yield</div>
      <div class="metric-value">{yield_2y:.2f}%</div>
      <div class="metric-sub">2-Year Constant Maturity</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">10Y-2Y Spread</div>
      <div class="metric-value {'positive' if spread_value >= 0 else 'negative'}">{spread_value:+.2f}%</div>
      <div class="metric-sub">Primary recession signal</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">3M Yield</div>
      <div class="metric-value">{yield_3m:.2f}%</div>
      <div class="metric-sub">3-Month Treasury Bill</div>
    </div>
  </div>

  <div class="alert-bar {'normal' if not is_inverted else 'inverted'}">
    {'<span>Yield curve is currently <strong>normal</strong>. Long-term rates exceed short-term rates. No inversion signal at present.</span>' if not is_inverted else '<span>Yield curve is currently <strong>inverted</strong>. Short-term rates exceed long-term rates. Historically this has preceded recessions by 6 to 24 months.</span>'}
  </div>

  <div class="tabs">
    <div class="tab active" onclick="switchTab(event, 'snapshot')">Current Snapshot</div>
    <div class="tab" onclick="switchTab(event, 'spread')">Spread History</div>
    <div class="tab" onclick="switchTab(event, 'compare')">Historical Comparison</div>
    <div class="tab" onclick="switchTab(event, 'inversion')">Inversion Analysis</div>
  </div>

  <div id="tab-snapshot" class="tab-content active">
    <div class="two-col">
      <div class="card">
        <div class="card-header">
          <div class="card-title">Yield Curve as of {data_date}</div>
          <div class="card-subtitle">U.S. Treasury yields across all maturities</div>
        </div>
        <div class="chart-container">
          <canvas id="curveChart" role="img" aria-label="Current U.S. Treasury yield curve">Current yield curve</canvas>
        </div>
        <div class="insight-box">
          <strong>Reading the curve:</strong> A normal upward-sloping curve reflects healthy economic expectations.
          An inverted curve, where short rates exceed long rates, has preceded every U.S. recession since the 1970s.
        </div>
      </div>
      <div class="card">
        <div class="card-header">
          <div class="card-title">Maturity Breakdown</div>
          <div class="card-subtitle">All six Treasury maturities</div>
        </div>
        <table>
          <thead><tr><th>Maturity</th><th>Series</th><th>Yield</th></tr></thead>
          <tbody>
            <tr><td class="label-col">3 Month</td><td class="label-col">DGS3MO</td><td>{current_yields[0]:.2f}%</td></tr>
            <tr><td class="label-col">1 Year</td><td class="label-col">DGS1</td><td>{current_yields[1]:.2f}%</td></tr>
            <tr><td class="label-col">2 Year</td><td class="label-col">DGS2</td><td>{current_yields[2]:.2f}%</td></tr>
            <tr><td class="label-col">5 Year</td><td class="label-col">DGS5</td><td>{current_yields[3]:.2f}%</td></tr>
            <tr><td class="label-col">10 Year</td><td class="label-col">DGS10</td><td>{current_yields[4]:.2f}%</td></tr>
            <tr><td class="label-col">30 Year</td><td class="label-col">DGS30</td><td>{current_yields[5]:.2f}%</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <div id="tab-spread" class="tab-content">
    <div class="card">
      <div class="card-header">
        <div class="card-title">10Y-2Y Spread, 2000 to Present</div>
        <div class="card-subtitle">Negative values indicate an inverted yield curve</div>
      </div>
      <div class="chart-container" style="height: 400px;">
        <canvas id="spreadChart" role="img" aria-label="Historical 10Y-2Y Treasury spread">Spread history</canvas>
      </div>
      <div class="insight-box">
        <strong>Inversion periods</strong> are shown in red. The 2006-2007 inversion came before the 2008 financial crisis.
        The 2022-2024 inversion was the deepest since the 1980s, driven by aggressive Fed rate hikes.
        The curve has since normalized as the Fed began cutting rates.
      </div>
    </div>
  </div>

  <div id="tab-compare" class="tab-content">
    <div class="card">
      <div class="card-header">
        <div class="card-title">Historical Comparison</div>
        <div class="card-subtitle">Compare the yield curve shape on any two trading days</div>
      </div>
      <div class="date-controls">
        <div>
          <div class="date-label">First Date</div>
          <input type="date" id="date1" value="2007-01-02" min="2000-01-01" max="{data_date}">
        </div>
        <div>
          <div class="date-label">Second Date</div>
          <input type="date" id="date2" value="{data_date}" min="2000-01-01" max="{data_date}">
        </div>
      </div>
      <button class="compare-btn" onclick="updateComparison()">Compare Curves</button>
      <div class="chart-container">
        <canvas id="compareChart" role="img" aria-label="Yield curve comparison">Comparison chart</canvas>
      </div>
      <div id="compare-insight" class="insight-box" style="margin-top: 1.25rem;"></div>
    </div>
  </div>

  <div id="tab-inversion" class="tab-content">
    <div class="three-col">
      <div class="metric-card">
        <div class="metric-label">Total Trading Days</div>
        <div class="metric-value">{total_days:,}</div>
        <div class="metric-sub">Since January 2000</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Days Inverted</div>
        <div class="metric-value negative">{total_inverted:,}</div>
        <div class="metric-sub">10Y-2Y spread below zero</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Time Inverted</div>
        <div class="metric-value">{pct_inverted:.1f}%</div>
        <div class="metric-sub">Of all trading days since 2000</div>
      </div>
    </div>
    <div class="card">
      <div class="card-header">
        <div class="card-title">Inversion Periods</div>
        <div class="card-subtitle">Consecutive trading days with negative 10Y-2Y spread</div>
      </div>
      <table>
        <thead><tr><th>Start</th><th>End</th><th>Trading Days</th><th>Deepest Inversion</th></tr></thead>
        <tbody>
          {''.join(f"""<tr>
            <td>{p['start']}</td><td>{p['end']}</td>
            <td>{p['days']}</td>
            <td class="negative">{p['min_spread']:.2f}%</td>
          </tr>""" for p in inversion_periods)}
        </tbody>
      </table>
      <div class="insight-box">
        <strong>Historical context:</strong> The 2022-2024 inversion began in July 2022 as the Federal Reserve
        raised rates from near zero to 5.25-5.50% to fight post-pandemic inflation.
        It was the longest inversion since the early 1980s. The curve normalized in late 2024 as the Fed began cutting rates.
      </div>
    </div>
  </div>

</main>

<div class="footer">
  <span>YC Monitor. Data: FRED, Federal Reserve Bank of St. Louis</span>
  <span>Alexander Devano Aryasena &copy; 2026 &nbsp;|&nbsp; Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC</span>
</div>

<script>
const DATES = {json.dumps(dates)};
const SPREADS = {json.dumps(spread_data)};
const MATURITIES = {json.dumps(maturities)};
const CURRENT_YIELDS = {json.dumps(current_yields)};
const ALL_YIELDS = {json.dumps(all_yields)};

const ACCENT = '#c9963a';
const GREEN = '#3ecf8e';
const RED = '#e05b5b';
const BLUE = '#6ea8f7';
const MUTED = '#76768a';
const MONO = "'DM Mono', monospace";

const tooltipDefaults = {{
  backgroundColor: '#1a1a1f',
  borderColor: 'rgba(255,255,255,0.08)',
  borderWidth: 1,
  titleColor: '#f0f0f4',
  bodyColor: MUTED,
  padding: 10
}};

const scaleDefaults = {{
  x: {{
    grid: {{ color: 'rgba(255,255,255,0.04)' }},
    ticks: {{ color: MUTED, font: {{ size: 11, family: MONO }} }}
  }},
  y: {{
    grid: {{ color: 'rgba(255,255,255,0.04)' }},
    ticks: {{ color: MUTED, font: {{ size: 11, family: MONO }}, callback: v => v.toFixed(2) + '%' }}
  }}
}};

new Chart(document.getElementById('curveChart'), {{
  type: 'line',
  data: {{
    labels: MATURITIES,
    datasets: [{{
      data: CURRENT_YIELDS,
      borderColor: ACCENT,
      backgroundColor: 'rgba(201,150,58,0.08)',
      borderWidth: 2,
      pointBackgroundColor: ACCENT,
      pointBorderColor: ACCENT,
      pointRadius: 5,
      pointHoverRadius: 7,
      fill: true,
      tension: 0.3
    }}]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{ ...tooltipDefaults, callbacks: {{ label: ctx => ctx.parsed.y.toFixed(2) + '%' }} }}
    }},
    scales: scaleDefaults
  }}
}});

const filteredDates = DATES.filter((_, i) => i % 5 === 0);
const filteredSpreads = SPREADS.filter((_, i) => i % 5 === 0);

new Chart(document.getElementById('spreadChart'), {{
  type: 'bar',
  data: {{
    labels: filteredDates,
    datasets: [{{
      data: filteredSpreads,
      backgroundColor: filteredSpreads.map(v => v < 0 ? 'rgba(224,91,91,0.7)' : 'rgba(201,150,58,0.6)'),
      borderWidth: 0,
      borderRadius: 1
    }}]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{ ...tooltipDefaults, callbacks: {{ label: ctx => ctx.parsed.y.toFixed(3) + '%' }} }}
    }},
    scales: {{
      x: {{
        grid: {{ color: 'rgba(255,255,255,0.04)' }},
        ticks: {{ color: MUTED, font: {{ size: 10, family: MONO }}, maxTicksLimit: 12, autoSkip: true }}
      }},
      y: {{
        grid: {{ color: 'rgba(255,255,255,0.04)' }},
        ticks: {{ color: MUTED, font: {{ size: 11, family: MONO }}, callback: v => v.toFixed(2) + '%' }}
      }}
    }}
  }}
}});

let compareChart = null;

function findClosestDate(target) {{
  const t = new Date(target).getTime();
  let closest = DATES[0];
  let minDiff = Infinity;
  for (const d of DATES) {{
    const diff = Math.abs(new Date(d).getTime() - t);
    if (diff < minDiff) {{ minDiff = diff; closest = d; }}
  }}
  return closest;
}}

function updateComparison() {{
  const d1 = document.getElementById('date1').value;
  const d2 = document.getElementById('date2').value;
  const closest1 = findClosestDate(d1);
  const closest2 = findClosestDate(d2);
  const yields1 = ALL_YIELDS[closest1];
  const yields2 = ALL_YIELDS[closest2];

  if (!yields1 || !yields2) {{
    document.getElementById('compare-insight').innerHTML =
      '<strong>No data found</strong> for one or both dates. Try a nearby trading day.';
    return;
  }}

  if (compareChart) compareChart.destroy();

  compareChart = new Chart(document.getElementById('compareChart'), {{
    type: 'line',
    data: {{
      labels: MATURITIES,
      datasets: [
        {{
          label: closest1,
          data: yields1,
          borderColor: ACCENT,
          backgroundColor: 'rgba(201,150,58,0.06)',
          borderWidth: 2,
          pointBackgroundColor: ACCENT,
          pointRadius: 5,
          fill: true,
          tension: 0.3
        }},
        {{
          label: closest2,
          data: yields2,
          borderColor: BLUE,
          backgroundColor: 'rgba(110,168,247,0.06)',
          borderWidth: 2,
          pointBackgroundColor: BLUE,
          pointRadius: 5,
          fill: true,
          tension: 0.3
        }}
      ]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{
          display: true,
          labels: {{ color: '#f0f0f4', font: {{ size: 12, family: MONO }}, boxWidth: 12, boxHeight: 2, padding: 20 }}
        }},
        tooltip: {{ ...tooltipDefaults, callbacks: {{ label: ctx => ctx.dataset.label + ': ' + ctx.parsed.y.toFixed(2) + '%' }} }}
      }},
      scales: scaleDefaults
    }}
  }});

  const idx1 = DATES.indexOf(closest1);
  const idx2 = DATES.indexOf(closest2);
  const s1 = idx1 >= 0 ? SPREADS[idx1] : null;
  const s2 = idx2 >= 0 ? SPREADS[idx2] : null;

  document.getElementById('compare-insight').innerHTML =
    `<strong>${{closest1}}:</strong> 10Y-2Y spread ${{s1 !== null ? s1.toFixed(3) + '%' : 'N/A'}} (${{s1 !== null ? (s1 >= 0 ? 'normal' : 'inverted') : 'unknown'}})
    &nbsp;&nbsp;
    <strong>${{closest2}}:</strong> 10Y-2Y spread ${{s2 !== null ? s2.toFixed(3) + '%' : 'N/A'}} (${{s2 !== null ? (s2 >= 0 ? 'normal' : 'inverted') : 'unknown'}})`;
}}

updateComparison();

function switchTab(event, name) {{
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  event.target.classList.add('active');
}}
</script>
</body>
</html>"""

output_path = "dashboard/index.html"
with open(output_path, "w") as f:
    f.write(html)

print(f"Dashboard generated: {output_path}")
print("Open dashboard/index.html in your browser")
