"""
demo_app.py — EcoSentinel AI Module · Local Demo UI

Run with:
    streamlit run demo_app.py

This is a development / testing harness for the AI analysis module.
It is NOT the production Streamlit app (that belongs to Member 4).
It lets you fill in a complaint, paste readings, and see the full
analyse_incident() output rendered in a browser.
"""

import json
import textwrap

import pandas as pd
import streamlit as st

from ai_module.ai_analysis import analyse_incident

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EcoSentinel · AI Module Demo",
    page_icon="🌿",
    layout="wide",
)

# ── Header ───────────────────────────────────────────────────────────────────
st.title("🌿 EcoSentinel — AI Analysis Module")
st.caption(
    "Development demo for the AI/ML analysis module. "
    "Fill in a complaint and readings, then click **Run Analysis**."
)
st.divider()

# ── Sidebar — complaint input ─────────────────────────────────────────────────
with st.sidebar:
    st.header("📋 Complaint Details")

    incident_id = st.text_input("Incident ID", value="ECO-001")
    complaint_type = st.selectbox(
        "Complaint Type",
        [
            "Smoke",
            "Dust",
            "Gas or unusual odour",
            "Industrial emissions",
            "Vehicle emissions",
            "Water pollution",
            "Noise pollution",
            "Other",
        ],
    )
    location = st.text_input("Location", value="Andheri, Mumbai")
    description = st.text_area(
        "Description",
        value="Thick black smoke near an industrial area — choking fumes visible from the road.",
        height=120,
    )
    timestamp = st.text_input("Timestamp (YYYY-MM-DD HH:MM)", value="2026-11-03 10:30")

    st.divider()
    st.header("⚙️ Options")
    use_history = st.toggle("Include synthetic history (anomaly detection)", value=True)
    show_raw_json = st.toggle("Show raw JSON output", value=False)

# ── Main area — readings input ────────────────────────────────────────────────
st.subheader("📡 Air-Quality Readings")
st.caption(
    "Edit the CSV below. Columns: **pollutant, value, station, unit**. "
    "Leave value blank or use `nan` to simulate missing data."
)

DEFAULT_CSV = textwrap.dedent("""\
    pollutant,value,station,unit
    PM2.5,280,Andheri,µg/m³
    PM10,420,Andheri,µg/m³
    NO2,95,Andheri,µg/m³
    SO2,-5,Andheri,µg/m³
    CO,nan,Andheri,mg/m³
    Toluene,80,Andheri,µg/m³
""")

csv_input = st.text_area("Readings CSV", value=DEFAULT_CSV, height=200)

# ── Build DataFrames ──────────────────────────────────────────────────────────
try:
    from io import StringIO
    readings_df = pd.read_csv(StringIO(csv_input))
except Exception as e:
    st.error(f"Could not parse readings CSV: {e}")
    st.stop()

# Optional synthetic history for anomaly detection
history_df: pd.DataFrame | None = None
if use_history:
    history_values = [45, 50, 48, 52, 47, 51, 49, 53, 46, 50, 48, 52]
    history_df = pd.DataFrame(
        [{"pollutant": "PM2.5", "value": v, "station": "Andheri"} for v in history_values]
    )
    st.caption(
        f"✅ Synthetic history loaded: {len(history_df)} PM2.5 readings for Andheri "
        "(mean ≈ 50 µg/m³ — current reading will look like a spike)."
    )

# ── Run button ────────────────────────────────────────────────────────────────
st.divider()
run = st.button("🔍 Run Analysis", type="primary", use_container_width=True)

if not run:
    st.info("👆 Fill in the complaint details in the sidebar, then click **Run Analysis**.")
    st.stop()

# ── Call analyse_incident() ───────────────────────────────────────────────────
complaint = {
    "incident_id": incident_id,
    "type": complaint_type,
    "location": location,
    "description": description,
    "timestamp": timestamp,
}

with st.spinner("Analysing…"):
    result = analyse_incident(complaint, readings_df, history_df)

# ── Render results ────────────────────────────────────────────────────────────

# ── Top metrics row ───────────────────────────────────────────────────────────
st.subheader("📊 Analysis Result")

col1, col2, col3, col4 = st.columns(4)

RISK_COLOURS = {
    "High": "🔴",
    "Medium": "🟡",
    "Low": "🟢",
    "Insufficient Data": "⚪",
}
QUALITY_COLOURS = {"Good": "🟢", "Partial": "🟡", "Poor": "🔴"}
CONF_COLOURS = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}

col1.metric(
    "Risk Level",
    f"{RISK_COLOURS.get(result['risk_level'], '')} {result['risk_level']}",
)
col2.metric(
    "Data Quality",
    f"{QUALITY_COLOURS.get(result['data_quality'], '')} {result['data_quality']}",
)
col3.metric(
    "Confidence",
    f"{CONF_COLOURS.get(result['confidence'], '')} {result['confidence']}",
)
col4.metric(
    "Human Review",
    "✅ Required" if result["requires_human_review"] else "❌ Not required",
)

# ── Pollution type & risk reason ─────────────────────────────────────────────
st.divider()
col_l, col_r = st.columns(2)
with col_l:
    st.markdown(f"**Pollution Type Resolved:** `{result['pollution_type']}`")
with col_r:
    st.markdown(f"**Incident ID:** `{result['incident_id']}`")

st.markdown(f"**Risk Reason:** {result['risk_reason']}")

# ── AI Explanation ────────────────────────────────────────────────────────────
st.divider()
st.subheader("🤖 AI Explanation")
st.info(result["ai_explanation"])

# ── Findings ─────────────────────────────────────────────────────────────────
st.divider()
st.subheader("🔎 Findings")

SEV_ICON = {
    "High": "🔴",
    "Normal": "🟢",
    "Info": "ℹ️",
    "Invalid": "⚠️",
    "Stale": "🕐",
    "Anomaly": "📈",
}

findings = result.get("findings", [])
if findings:
    rows = []
    for f in findings:
        rows.append(
            {
                "": SEV_ICON.get(f.get("severity", ""), "•"),
                "Pollutant": f.get("pollutant") or "—",
                "Value": f.get("value") if f.get("value") is not None else "—",
                "Unit": f.get("unit") or "—",
                "Station": f.get("station") or "—",
                "Severity": f.get("severity", "—"),
                "Reason": f.get("reason", ""),
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.write("No findings.")

# ── Anomalies ─────────────────────────────────────────────────────────────────
st.divider()
st.subheader("📈 Anomalies (vs. Historical Data)")

anomalies = result.get("anomalies", [])
if anomalies:
    rows = []
    for a in anomalies:
        rows.append(
            {
                "Pollutant": a.get("pollutant"),
                "Value": a.get("value"),
                "Unit": a.get("unit") or "µg/m³",
                "Station": a.get("station"),
                "Z-Score": a.get("z_score"),
                "Hist. Mean": a.get("historical_mean"),
                "Hist. Std": a.get("historical_std"),
                "n (history)": a.get("n_history_points"),
                "Reason": a.get("reason"),
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.write("No anomalies detected (or insufficient historical data).")

# ── Compliance ────────────────────────────────────────────────────────────────
st.divider()
st.subheader("⚖️ Compliance Check")

compliance = result.get("compliance", {})
st.caption(compliance.get("summary", ""))

comp_results = compliance.get("results", [])
if comp_results:
    rows = []
    for c in comp_results:
        rows.append(
            {
                "Pollutant": c.get("pollutant"),
                "Value": c.get("value"),
                "Unit": c.get("unit") or "—",
                "Station": c.get("station"),
                "Status": c.get("status"),
                "Threshold": c.get("threshold") or "None (TODO)",
                "Standard": c.get("standard") or "—",
                "Reason": c.get("reason"),
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    if not compliance.get("assessed"):
        st.warning(
            "⚠️ Compliance thresholds are set to `None` in `config.py`. "
            "Fill in verified CPCB NAAQS values to enable full compliance checks.",
            icon="📋",
        )

# ── Recommendations ───────────────────────────────────────────────────────────
st.divider()
st.subheader("✅ Recommendations")

recs = result.get("recommendations", [])
if recs:
    for i, rec in enumerate(recs, 1):
        st.markdown(f"**{i}.** {rec}")
else:
    st.write("No recommendations generated.")

# ── Raw JSON ──────────────────────────────────────────────────────────────────
if show_raw_json:
    st.divider()
    st.subheader("🗂️ Raw JSON Output")
    st.code(json.dumps(result, indent=2, default=str), language="json")

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "EcoSentinel AI Module · Hackathon Demo · "
    "This is preliminary automated triage only — not an official regulatory finding."
)

