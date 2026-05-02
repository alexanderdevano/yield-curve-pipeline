import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from pyathena import connect

# page config 
st.set_page_config(
    page_title="U.S. Treasury Yield Curve Monitor",
    layout="wide"
)

# connect to Athena
@st.cache_resource

def get_connection():
    return connect(
        s3_staging_dir="s3://yield-curve-athena-results/",
        region_name="ap-southeast-2"
    )

# load data
@st.cache_data(ttl=3600)
def load_spreads():
    conn = get_connection()
    return pd.read_sql("SELECT * FROM yield_curve.yield_spreads ORDER BY date", conn)

@st.cache_data(ttl=3600)
def load_inversion():
    conn = get_connection()
    return pd.read_sql("SELECT * FROM yield_curve.inversion_flags ORDER BY date", conn)

# load
spreads = load_spreads()
inversion = load_inversion()

# latest data
latest = spreads.iloc[-1]
is_inverted = latest['spread_10y_2y'] < 0

# header
st.title("U.S. Treasury Yield Curve Monitor")
st.caption(f"Data as of {latest['date']} | Source: FRED, Federal Reserve Bank of St. Louis")

st.divider()

# key metrics row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="10Y Yield",
        value=f"{latest['yield_10y']:.2f}%"
    )
with col2:
    st.metric(
        label="2Y Yield",
        value=f"{latest['yield_2y']:.2f}%"
    )
with col3:
    st.metric(
        label="10Y-2Y Spread",
        value=f"{latest['spread_10y_2y']:.2f}%",
        delta=None
    )
with col4:
    status = "Inverted" if is_inverted else "Normal"
    st.metric(
        label="Curve Status",
        value=status
    )

st.divider()

# status bar
if is_inverted:
    st.error(f"The yield curve is currently inverted. Historically this has preceded recessions by 6-24 months.")
else:
    st.success(f"The yield curve is currently normal — short-term rates are below long-term rates.")

# tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "Current Snapshot",
    "Spread History",
    "Historical Comparison",
    "Inversion Analysis"
])

with tab1:
    st.subheader("Current Yield Curve")
    st.caption("Each point represents the yield for a specific Treasury maturity as of the latest trading day.")

    # prepare current curve data
    maturities = ["3M", "1Y", "2Y", "5Y", "10Y", "30Y"]
    yields = [
        latest['yield_3m'],
        latest['yield_1y'],
        latest['yield_2y'],
        latest['yield_5y'],
        latest['yield_10y'],
        latest['yield_30y']
    ]

    # build plotly chart
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=maturities,
        y=yields,
        mode='lines+markers',
        line=dict(color='#2196F3', width=2),
        marker=dict(size=8),
        hovertemplate='%{x}: %{y:.2f}%<extra></extra>'
    ))

    fig.update_layout(
        title=f"U.S. Treasury Yield Curve — {latest['date']}",
        xaxis_title="Maturity",
        yaxis_title="Yield (%)",
        yaxis_tickformat=".2f",
        hovermode="x unified",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

    # explanation
    st.markdown("""
    A normal yield curve slopes upward — longer maturities pay higher yields.
    An inverted curve (downward sloping) has historically preceded U.S. recessions.
    """)

with tab2:
    st.subheader("10Y-2Y Spread History")
    st.caption("The spread between 10-year and 2-year Treasury yields. Negative values indicate an inverted curve.")

    fig2 = go.Figure()

    # spread line
    fig2.add_trace(go.Scatter(
        x=spreads['date'],
        y=spreads['spread_10y_2y'],
        mode='lines',
        name='10Y-2Y Spread',
        line=dict(color='#2196F3', width=1.5),
        hovertemplate='%{x}: %{y:.2f}%<extra></extra>'
    ))

    # zero line
    fig2.add_hline(
        y=0,
        line_dash="dash",
        line_color="red",
        annotation_text="Inversion threshold",
        annotation_position="bottom right"
    )

    # shade inverted periods
    inverted_periods = inversion[inversion['is_inverted_2y'] == True]
    if not inverted_periods.empty:
        fig2.add_trace(go.Scatter(
            x=pd.concat([inverted_periods['date'], inverted_periods['date'][::-1]]),
            y=pd.concat([inverted_periods['spread_10y_2y'], 
                        pd.Series([0] * len(inverted_periods))]),
            fill='toself',
            fillcolor='rgba(255,0,0,0.1)',
            line=dict(color='rgba(255,255,255,0)'),
            name='Inverted periods',
            showlegend=True
        ))

    fig2.update_layout(
        title="10Y-2Y Treasury Spread (2000 — Present)",
        xaxis_title="Date",
        yaxis_title="Spread (%)",
        yaxis_tickformat=".2f",
        hovermode="x unified",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=450
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("""
    When the spread drops below zero (red dashed line) the curve is inverted.
    Red shaded areas show inversion periods. Every U.S. recession since the 1970s 
    was preceded by a yield curve inversion.
    """)

with tab3:
    st.subheader("Historical Curve Comparison")
    st.caption("Compare the yield curve shape on any two dates.")

    col1, col2 = st.columns(2)
    with col1:
        date1 = st.date_input(
            "First date",
            value=pd.to_datetime("2007-01-01"),
            min_value=pd.to_datetime(spreads['date'].min()),
            max_value=pd.to_datetime(spreads['date'].max())
        )
    with col2:
        date2 = st.date_input(
            "Second date",
            value=pd.to_datetime(spreads['date'].max()),
            min_value=pd.to_datetime(spreads['date'].min()),
            max_value=pd.to_datetime(spreads['date'].max())
        )

    spreads['date'] = pd.to_datetime(spreads['date'])
    row1 = spreads[spreads['date'] == pd.to_datetime(date1)]
    row2 = spreads[spreads['date'] == pd.to_datetime(date2)]

    if row1.empty:
        st.warning(f"No data for {date1} — markets may have been closed. Try a nearby date.")
    elif row2.empty:
        st.warning(f"No data for {date2} — markets may have been closed. Try a nearby date.")
    else:
        row1 = row1.iloc[0]
        row2 = row2.iloc[0]

        maturities = ["3M", "1Y", "2Y", "5Y", "10Y", "30Y"]

        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=maturities,
            y=[row1['yield_3m'], row1['yield_1y'], row1['yield_2y'],
               row1['yield_5y'], row1['yield_10y'], row1['yield_30y']],
            mode='lines+markers',
            name=str(date1),
            line=dict(color='#2196F3', width=2),
            marker=dict(size=8),
            hovertemplate='%{x}: %{y:.2f}%<extra></extra>'
        ))
        fig3.add_trace(go.Scatter(
            x=maturities,
            y=[row2['yield_3m'], row2['yield_1y'], row2['yield_2y'],
               row2['yield_5y'], row2['yield_10y'], row2['yield_30y']],
            mode='lines+markers',
            name=str(date2),
            line=dict(color='#FF9800', width=2),
            marker=dict(size=8),
            hovertemplate='%{x}: %{y:.2f}%<extra></extra>'
        ))
        fig3.update_layout(
            title="Yield Curve Comparison",
            xaxis_title="Maturity",
            yaxis_title="Yield (%)",
            yaxis_tickformat=".2f",
            hovermode="x unified",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=400
        )
        st.plotly_chart(fig3, use_container_width=True)

with tab4:
    st.subheader("Inversion Analysis")
    st.caption("Historical periods where the 10Y-2Y spread was negative.")

    # summary metrics
    total_inverted = inversion['is_inverted_2y'].sum()
    total_days = len(inversion)
    pct_inverted = (total_inverted / total_days) * 100

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Trading Days", f"{total_days:,}")
    with col2:
        st.metric("Days Inverted", f"{total_inverted:,}")
    with col3:
        st.metric("% Time Inverted", f"{pct_inverted:.1f}%")

    st.divider()

    # inversion periods table
    st.markdown("**Inversion Periods (10Y-2Y)**")

    inversion['date'] = pd.to_datetime(inversion['date'])
    inversion_only = inversion[inversion['is_inverted_2y'] == True].copy()

    # group into continuous periods
    inversion_only['period'] = (
        inversion_only['date'].diff().dt.days > 5
    ).cumsum()

    periods = inversion_only.groupby('period').agg(
        start=('date', 'min'),
        end=('date', 'max'),
        days=('date', 'count'),
        avg_spread=('spread_10y_2y', 'mean'),
        min_spread=('spread_10y_2y', 'min')
    ).reset_index(drop=True)

    periods['start'] = periods['start'].dt.strftime('%Y-%m-%d')
    periods['end'] = periods['end'].dt.strftime('%Y-%m-%d')
    periods['avg_spread'] = periods['avg_spread'].round(2)
    periods['min_spread'] = periods['min_spread'].round(2)

    periods.columns = ['Start', 'End', 'Trading Days', 'Avg Spread (%)', 'Deepest Inversion (%)']

    st.dataframe(periods, use_container_width=True)

    st.markdown("""
    **Note:** Inversion periods are defined as consecutive trading days where the 
    10Y-2Y spread was negative. The deepest inversion shows the most negative spread 
    recorded during each period.
    """)