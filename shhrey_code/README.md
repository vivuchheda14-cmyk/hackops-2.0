# EcoSentinel — AI Analysis Module

> **For the hackathon team:** This is Module 3 of 4. It exposes a single
> function — `analyse_incident()` — that Member 4 calls from the Streamlit
> app. **Do not modify other team members' files.**

---

## Quick Start (install + run in 60 seconds)

```bash
# 1. Install dependencies (from the project root)
pip install -r requirements.txt

# 2. Run the demo
python demo.py

# 3. Run the test suite
python -m pytest tests/test_ai_analysis.py -v
```

Expected test result: **17 passed**.

---

## File Structure

```
ai_module/
    __init__.py              # package marker
    ai_analysis.py           # ← main entry point (analyse_incident)
    complaint_classifier.py  # keyword-based complaint classification
    pollution_analysis.py    # reading validation and threshold flagging
    anomaly_detection.py     # Z-score anomaly detection vs. history
    risk_assessment.py       # Low/Medium/High/Insufficient Data triage
    compliance.py            # NAAQS compliance check (thresholds = None)
    recommendations.py       # evidence-based action recommendations
    config.py                # ALL thresholds, keywords, and settings

tests/
    test_ai_analysis.py      # 17 pytest test cases

demo.py                      # runnable sample call
requirements.txt
README.md                    # this file
```

---

## Integration Snippet for Member 4

```python
import pandas as pd
from ai_module.ai_analysis import analyse_incident

# --- build complaint dict (from citizen portal) ---
complaint = {
    "incident_id": "ECO-001",
    "type": "Smoke",                         # citizen-selected type
    "location": "Andheri, Mumbai",
    "description": "Thick black smoke near an industrial area",
    "timestamp": "2026-11-03 10:30",         # format: YYYY-MM-DD HH:MM
}

# --- build readings DataFrame (from air quality dashboard) ---
readings = pd.DataFrame([
    {"pollutant": "PM2.5", "value": 280.0, "station": "Andheri", "unit": "µg/m³"},
    {"pollutant": "PM10",  "value": 420.0, "station": "Andheri", "unit": "µg/m³"},
])

# --- optional: pass historical data for anomaly detection ---
# history = pd.DataFrame(...)  # same columns + multiple rows per pollutant

result = analyse_incident(complaint, readings)          # or pass history=history
# result = analyse_incident(complaint, readings, history)

# --- use in Streamlit ---
# st.metric("Risk Level", result["risk_level"])
# st.write(result["ai_explanation"])
# st.json(result["compliance"])
# for rec in result["recommendations"]:
#     st.write("•", rec)
```

> **result is a plain Python dict — no Streamlit objects inside.**
> It is safe to `st.json(result)`, `json.dumps(result)`, or pass individual
> keys to any UI component.

---

## Input Contract

### `complaint` (dict)

| Key | Type | Description |
|---|---|---|
| `incident_id` | `str` | Unique incident identifier, e.g. `"ECO-001"` |
| `type` | `str` | Citizen-selected category (see categories below) |
| `location` | `str` | Free-text location, e.g. `"Andheri, Mumbai"` |
| `description` | `str` | Free-text complaint description |
| `timestamp` | `str` | Format: `"YYYY-MM-DD HH:MM"` |

**Complaint categories:** Smoke · Dust · Gas or unusual odour · Industrial emissions · Vehicle emissions · Water pollution · Noise pollution · Other

### `readings` (pd.DataFrame)

Required columns (aliases accepted — see below):

| Column | Aliases accepted | Description |
|---|---|---|
| `pollutant` | `pollutant_id`, `pollutant_name`, `parameter` | Pollutant name |
| `value` | `pollutant_avg`, `avg_value`, `avg`, `reading` | Numeric reading |
| `station` | `station_name`, `site`, `location` | Station name |
| `last_update` | `last_updated`, `timestamp`, `updated_at` | Optional timestamp |
| `unit` | — | Optional unit string (e.g. `"µg/m³"`) |

Assumed units: `µg/m³` for particulates and gases; `mg/m³` for CO.

### `history` (pd.DataFrame | None)

Same columns as `readings`, but with **multiple rows per (pollutant, station)**
across different timestamps. At least 10 rows per pair are needed for
Z-score analysis; otherwise anomaly detection is skipped gracefully.

---

## Output Contract

`analyse_incident()` always returns a dict with **exactly** these keys:

```python
{
    "incident_id":         str,                   # echoed from complaint
    "pollution_type":      str,                   # resolved classification
    "risk_level":          "Low" | "Medium" | "High" | "Insufficient Data",
    "risk_reason":         str,                   # plain-language reason
    "confidence":          "High" | "Medium" | "Low",
    "findings": [                                 # list of finding dicts
        {
            "pollutant": str | None,
            "value":     float | None,
            "unit":      str | None,
            "station":   str | None,
            "reason":    str,
            "severity":  "High" | "Normal" | "Info" | "Invalid" | "Stale" | "Anomaly",
        }
    ],
    "anomalies": [                                # same shape as findings
        {
            "pollutant": str, "value": float, "unit": str, "station": str,
            "z_score": float, "historical_mean": float, "historical_std": float,
            "n_history_points": int, "reason": str, "severity": "Anomaly",
        }
    ],
    "compliance": {                               # from compliance.py
        "results": [...],
        "summary": str,
        "assessed": bool,
    },
    "recommendations":    [str],                  # ordered action list
    "ai_explanation":     str,                    # LLM or template explanation
    "data_quality":       "Good" | "Partial" | "Poor",
    "requires_human_review": bool,
}
```

**Key definitions:**
- `data_quality` — Good: ≥80% valid, fresh readings. Partial: ≥40% or some
  stale. Poor: <40% valid or no data at all.
- `confidence` — derived from data quality; lowered one level when station
  matching fell back to all stations.
- `requires_human_review` — `False` only when `risk_level == "Low"` AND
  `data_quality == "Good"`. Always `True` for Insufficient Data.

---

## Setting the Anthropic API Key (optional)

The module works fully **without** an API key — it falls back to a
deterministic template explanation.

To enable LLM explanations:

**Windows (PowerShell):**
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
python demo.py
```

**Persistent (set in system environment):**
Go to System → Advanced → Environment Variables → add `ANTHROPIC_API_KEY`.

The key is read at runtime via `os.environ.get("ANTHROPIC_API_KEY")` in
[`ai_analysis.py`](ai_module/ai_analysis.py). It is never hardcoded.

---

## Filling in Compliance Thresholds

All NAAQS threshold values in [`config.py`](ai_module/config.py) are
currently `None` placeholders:

```python
# config.py — NAAQS_THRESHOLDS section
"PM2.5": {
    "limit": None,   # TODO: verify from CPCB NAAQS before use
    ...
}
```

> **⚠️ Important:** Do NOT guess or use values from memory.
> Verify every limit from the official CPCB document:
> https://cpcb.nic.in/naaqs/
>
> Once verified, replace `None` with the numeric value. The compliance
> module will automatically start comparing readings against it.

Similarly, `ALERT_THRESHOLDS` (for basic flagging) are `None`; the module
currently falls back to `INDICATIVE_HIGH_THRESHOLDS` which are rough
order-of-magnitude values. Replace them with verified figures before any
production or regulatory use.

---

## Configuring the Module

All tuneable parameters live in [`config.py`](ai_module/config.py):

| Setting | Default | Description |
|---|---|---|
| `STALENESS_LIMIT_HOURS` | `24` | Hours before a reading is flagged stale |
| `ANOMALY_MIN_HISTORY_POINTS` | `10` | Min history rows for Z-score analysis |
| `ANOMALY_ZSCORE_THRESHOLD` | `3.0` | Z-score threshold for anomaly flag |
| `ANOMALY_ROLLING_WINDOW` | `5` | Rolling window size (future use) |
| `DATA_QUALITY_GOOD_THRESHOLD` | `0.8` | Fraction of valid readings for "Good" |
| `DATA_QUALITY_PARTIAL_THRESHOLD` | `0.4` | Fraction for "Partial" (else "Poor") |
| `COMPLAINT_KEYWORDS` | dict | Add/edit keyword lists per category |
| `SEVERITY_KEYWORDS` | list | Words that raise risk level |

---

## Design Decisions (for the team)

| Decision | Reason |
|---|---|
| No Isolation Forest | Not enough data in a hackathon / live demo setting |
| Z-score anomaly detection | Simple, interpretable, works with ~10 points |
| Thresholds = `None` | Never fabricate regulatory numbers |
| Template fallback for LLM | App must run with zero API keys |
| Keyword classifier | Fast, deterministic, no external calls needed |
| Returns plain dict | Keeps computation and Streamlit presentation separate |

---

## Running Tests

```bash
python -m pytest tests/test_ai_analysis.py -v
```

All 17 tests must pass before integration. Test cases cover:

| # | Case |
|---|---|
| 1 | Smoke + elevated PM2.5 → High/Medium risk, PM2.5 in findings |
| 2 | Dust + elevated PM10 → PM10 flagged |
| 3 | Normal readings → Low/Medium risk, no High-severity findings |
| 4 | Empty DataFrame → Insufficient Data, Poor quality, human review |
| 5 | NaN values → reported as invalid, never zero, Partial/Poor quality |
| 6 | Negative readings → excluded and reported |
| 7 | Unknown pollutant → kept, marked "no reference available" |
| 8 | None readings → Insufficient Data, recommendations include measurements |
| + | Type/description mismatch → description wins, mismatch in findings |
| + | Water/noise complaint → Insufficient Data, domain-specific recs |
| + | LLM unavailable → template explanation returned (no crash) |
| + | Column aliases → normalised correctly |
| + | No matching station → confidence lowered, fallback noted |
| + | Sufficient history → anomaly detected |
| + | Insufficient history → no anomaly, graceful message |
| + | Pollutant name aliases → normalised to canonical |
| + | Indicative thresholds used when ALERT_THRESHOLDS = None |

