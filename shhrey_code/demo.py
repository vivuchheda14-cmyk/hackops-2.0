"""
demo.py — Sample call demonstrating the EcoSentinel AI Analysis Module.

Run from the project root:
    python demo.py

This script prints the full analyse_incident() output so Member 4 can
see exactly what to expect before wiring it into the Streamlit app.
"""

import json
import pandas as pd
from ai_module.ai_analysis import analyse_incident

# ---------------------------------------------------------------------------
# Sample complaint (as would come from the citizen portal)
# ---------------------------------------------------------------------------
complaint = {
    "incident_id": "ECO-001",
    "type": "Smoke",
    "location": "Andheri, Mumbai",
    "description": "Thick black smoke near an industrial area — choking fumes",
    "timestamp": "2026-11-03 10:30",
}

# ---------------------------------------------------------------------------
# Sample sensor readings (as would come from the air quality dashboard)
# Values are illustrative, NOT live observations.
# ---------------------------------------------------------------------------
readings = pd.DataFrame([
    {"pollutant": "PM2.5", "value": 280.0, "station": "Andheri", "unit": "µg/m³",
     "last_update": "2026-11-03 09:00"},
    {"pollutant": "PM10",  "value": 420.0, "station": "Andheri", "unit": "µg/m³",
     "last_update": "2026-11-03 09:00"},
    {"pollutant": "NO2",   "value": 95.0,  "station": "Andheri", "unit": "µg/m³",
     "last_update": "2026-11-03 09:00"},
    {"pollutant": "SO2",   "value": -5.0,  "station": "Andheri", "unit": "µg/m³",
     "last_update": "2026-11-03 09:00"},  # invalid: negative
    {"pollutant": "CO",    "value": float("nan"), "station": "Andheri",
     "last_update": "2026-11-03 09:00"},  # invalid: NaN
    {"pollutant": "Toluene", "value": 80.0, "station": "Andheri",
     "last_update": "2026-11-03 09:00"},  # unknown pollutant
])

# ---------------------------------------------------------------------------
# Optional: small historical dataset for anomaly detection
# (in production, pass a larger DataFrame from your database)
# ---------------------------------------------------------------------------
history_values = [45, 50, 48, 52, 47, 51, 49, 53, 46, 50, 48, 52]
history = pd.DataFrame([
    {"pollutant": "PM2.5", "value": v, "station": "Andheri"}
    for v in history_values
])

# ---------------------------------------------------------------------------
# Run analysis
# ---------------------------------------------------------------------------
print("=" * 60)
print("EcoSentinel AI Analysis — Demo Call")
print("=" * 60)

result = analyse_incident(complaint, readings, history)

# Print the full structured result
print(json.dumps(result, indent=2, default=str))

print("\n" + "=" * 60)
print("AI Explanation (also in result['ai_explanation']):")
print("=" * 60)
print(result["ai_explanation"])

print("\n" + "=" * 60)
print("Integration snippet for Member 4 (Streamlit):")
print("=" * 60)
print("""
from ai_module.ai_analysis import analyse_incident

result = analyse_incident(complaint, readings)
# result is a plain Python dict — no Streamlit objects.
# Pass keys to your UI components, e.g.:
#   st.metric("Risk Level", result["risk_level"])
#   st.write(result["ai_explanation"])
#   st.json(result["compliance"])
""")

