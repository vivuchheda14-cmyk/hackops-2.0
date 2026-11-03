"""
EcoSentinel - Environmental Intelligence & Compliance Management System
Module: Member 2 - Air Quality Dashboard (dashboard.py)

Responsibilities:
1. Provide an interactive Streamlit UI for environmental monitoring.
2. Display monitoring stations, AQI, PM2.5, and PM10 metrics.
3. Render interactive Plotly charts for pollutant concentrations.
4. Display data quality warnings, CPCB compliance thresholds, and fallback notices.
5. Gracefully handle empty or partially missing data without crashing.
"""

import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Ensure current directory is on Python path so 'from data import ...' works reliably
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# CONTRACT IMPORT: Do not put API-fetching logic directly inside dashboard.py
from data import get_air_quality_data


# ==============================================================================
# STREAMLIT PAGE CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="EcoSentinel Air Quality Dashboard",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling for high-visibility environmental metric cards
st.markdown(
    """
    <style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 12px 16px;
        border-left: 5px solid #2e7d32;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 10px;
    }
    .metric-title {
        font-size: 0.85rem;
        color: #555555;
        font-weight: 600;
        text-transform: uppercase;
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1b5e20;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #777777;
    }
    </style>
    """,
    unsafe_allow_html=True
)


def get_aqi_category(aqi_val: float) -> tuple:
    """
    Returns the CPCB National Air Quality Index (NAQI) category and color code.
    """
    if pd.isna(aqi_val):
        return "Unknown / N/A", "#9e9e9e"
    if aqi_val <= 50:
        return "Good", "#2e7d32"  # Green
    if aqi_val <= 100:
        return "Satisfactory", "#558b2f"  # Light green
    if aqi_val <= 200:
        return "Moderate", "#f9a825"  # Yellow
    if aqi_val <= 300:
        return "Poor", "#ef6c00"  # Orange
    if aqi_val <= 400:
        return "Very Poor", "#c62828"  # Red
    return "Severe", "#6a1b9a"  # Purple / Maroon


# ==============================================================================
# DATA INGESTION (CACHED)
# ==============================================================================
@st.cache_data(ttl=300)
def load_data() -> pd.DataFrame:
    """
    Fetches and cleans air quality data via Member 2's data module.
    Cached for 5 minutes (300s) to avoid API rate limits.
    """
    return get_air_quality_data()


# Top Header
st.title("🌿 EcoSentinel Air Quality Dashboard")
st.markdown("Real-time Environmental Intelligence, Compliance & Air Quality Monitoring")

# Fetch data safely
with st.spinner("Retrieving air quality telemetry..."):
    df = load_data()

# Handle empty data scenario gracefully
if df is None or df.empty:
    st.error("⚠️ **No Data Available**: The air quality pipeline returned an empty dataset.")
    st.info("Please verify your internet connection or check your API settings in `.env`.")
    st.stop()

# Check for sample/fallback status
is_sample_data = getattr(df, "attrs", {}).get("is_sample", False)
if is_sample_data:
    st.warning(
        "⚠️ **Notice: Operating in Demonstration / Sample Mode.** "
        "The live CPCB / data.gov.in API is currently unreachable or unconfigured. "
        "Displaying calibrated benchmark sample records. (Configure `DATAGOV_API_KEY` in `.env` for live feeds)."
    )

# ==============================================================================
# SIDEBAR CONTROLS & STATION SELECTOR
# ==============================================================================
st.sidebar.header("🔍 Monitoring Controls")

available_stations = sorted([str(s) for s in df["station"].dropna().unique()])

if not available_stations:
    st.sidebar.error("No active stations found in data stream.")
    st.stop()

selected_station = st.sidebar.selectbox(
    "Select Monitoring Station:",
    options=available_stations,
    index=0
)

# Manual data reload trigger
if st.sidebar.button("🔄 Refresh Telemetry"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 📌 NAQI Reference Limits")
st.sidebar.markdown(
    """
    - **PM2.5 (24h Standard):** 60 µg/m³
    - **PM10 (24h Standard):** 100 µg/m³
    - **Good AQI:** 0 – 50
    - **Moderate AQI:** 101 – 200
    - **Severe AQI:** 401 – 500
    """
)

# Filter dataset for selected station
station_df = df[df["station"] == selected_station].copy()

# ==============================================================================
# KPI METRICS ROW (AQI, PM2.5, PM10, LATEST TIMESTAMP)
# ==============================================================================
# Extract latest values for key pollutants
def extract_pollutant_val(sub_df: pd.DataFrame, pollutant_name: str):
    matches = sub_df[sub_df["pollutant"].str.upper() == pollutant_name.upper()]
    if not matches.empty:
        val = matches.iloc[0]["value"]
        if pd.notna(val):
            return float(val)
    return None

def extract_aqi_val(sub_df: pd.DataFrame):
    # Check if 'aqi' column has valid non-null numbers
    valid_aqi = sub_df["aqi"].dropna()
    if not valid_aqi.empty:
        return float(valid_aqi.iloc[0])
    return None

latest_timestamp = station_df["timestamp"].dropna().iloc[0] if not station_df["timestamp"].dropna().empty else "N/A"
pm25_val = extract_pollutant_val(station_df, "PM2.5")
pm10_val = extract_pollutant_val(station_df, "PM10")
aqi_val = extract_aqi_val(station_df)

aqi_cat, aqi_color = get_aqi_category(aqi_val)

st.subheader(f"📍 Station: {selected_station}")
st.caption(f"🕒 Latest Observation Timestamp: **{latest_timestamp}**")

col1, col2, col3, col4 = st.columns(4)

with col1:
    aqi_display = f"{int(aqi_val)}" if aqi_val is not None else "N/A"
    st.markdown(
        f"""
        <div class="metric-card" style="border-left-color: {aqi_color};">
            <div class="metric-title">Air Quality Index (AQI)</div>
            <div class="metric-val" style="color: {aqi_color};">{aqi_display}</div>
            <div class="metric-sub" style="font-weight: 600; color: {aqi_color};">{aqi_cat}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    pm25_display = f"{pm25_val:.1f} µg/m³" if pm25_val is not None else "N/A"
    delta_pm25 = f"{(pm25_val - 60):+.1f} vs limit" if pm25_val is not None else ""
    st.metric(
        label="PM2.5 Concentration",
        value=pm25_display,
        delta=delta_pm25 if pm25_val is not None else None,
        delta_color="inverse"
    )

with col3:
    pm10_display = f"{pm10_val:.1f} µg/m³" if pm10_val is not None else "N/A"
    delta_pm10 = f"{(pm10_val - 100):+.1f} vs limit" if pm10_val is not None else ""
    st.metric(
        label="PM10 Concentration",
        value=pm10_display,
        delta=delta_pm10 if pm10_val is not None else None,
        delta_color="inverse"
    )

with col4:
    pollutant_count = station_df["pollutant"].dropna().nunique()
    st.metric(
        label="Tracked Pollutants",
        value=pollutant_count,
        delta="Active Sensors"
    )

# ==============================================================================
# DATA QUALITY & COMPLIANCE WARNINGS
# ==============================================================================
warnings = []
if aqi_val is None:
    warnings.append("⚠️ AQI calculation is unavailable for this station (missing sensor input).")
if pm25_val is None:
    warnings.append("⚠️ PM2.5 readings are missing or not reported.")
elif pm25_val > 60:
    warnings.append(f"🚨 **Compliance Alert**: PM2.5 reading ({pm25_val:.1f} µg/m³) exceeds the NAAQS 24-hour limit (60 µg/m³).")

if pm10_val is None:
    warnings.append("⚠️ PM10 readings are missing or not reported.")
elif pm10_val > 100:
    warnings.append(f"🚨 **Compliance Alert**: PM10 reading ({pm10_val:.1f} µg/m³) exceeds the NAAQS 24-hour limit (100 µg/m³).")

if warnings:
    with st.expander("⚠️ Data Quality & Regulatory Warnings", expanded=True):
        for w in warnings:
            st.write(w)

# ==============================================================================
# VISUALIZATIONS
# ==============================================================================
tab1, tab2, tab3 = st.tabs(["📊 Station Readings", "🌐 Cross-Station Comparison", "📋 Raw Data Stream"])

with tab1:
    st.markdown("#### Pollutant Profile at Selected Station")
    plot_df = station_df.dropna(subset=["value"]).copy()

    if not plot_df.empty:
        fig_station = px.bar(
            plot_df,
            x="pollutant",
            y="value",
            color="pollutant",
            text="value",
            labels={"pollutant": "Pollutant Parameter", "value": "Concentration (µg/m³)"},
            title=f"Current Pollutant Concentrations — {selected_station}"
        )
        fig_station.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        fig_station.update_layout(showlegend=False, yaxis=dict(title="Concentration (µg/m³)"))
        st.plotly_chart(fig_station, use_container_width=True)
    else:
        st.info("No numeric pollutant readings available to chart for this station.")

with tab2:
    st.markdown("#### Comparative Analysis Across All Monitored Stations")
    # Compare PM2.5 and PM10 across all stations
    pm_df = df[df["pollutant"].isin(["PM2.5", "PM10"])].dropna(subset=["value"]).copy()

    if not pm_df.empty:
        fig_compare = px.bar(
            pm_df,
            x="station",
            y="value",
            color="pollutant",
            barmode="group",
            labels={"station": "Monitoring Station", "value": "Concentration (µg/m³)"},
            title="PM2.5 & PM10 Levels by Station"
        )
        # Add regulatory benchmark reference lines
        fig_compare.add_hline(y=60, line_dash="dash", line_color="orange", annotation_text="PM2.5 Limit (60)")
        fig_compare.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="PM10 Limit (100)")
        fig_compare.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(fig_compare, use_container_width=True)
    else:
        st.info("Insufficient PM data across stations for comparative visualization.")

with tab3:
    st.markdown("#### Standardized DataFrame Contract Inspector")
    st.caption("Standardized schema provided to AI Analysis (Member 3) and Backend (Member 4).")
    st.dataframe(df, use_container_width=True)

    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Clean Telemetry (CSV)",
        data=csv_data,
        file_name="ecosentinel_clean_air_telemetry.csv",
        mime="text/csv"
    )

