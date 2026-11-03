# 🌿 EcoSentinel – AI-Powered Air Pollution Monitor

EcoSentinel is a citizen-facing, officer-managed environmental incident management system built for a hackathon in a single Python/Streamlit application.

## Team

| Member | Responsibility |
|--------|----------------|
| Member 1 | `citizen_portal.py` – Citizen complaint form |
| Member 2 | `data.py`, `dashboard.py` – CPCB data & charts |
| Member 3 | `ai_analysis.py`, `compliance.py` – AI & compliance |
| Member 4 | `app.py`, `database.py`, `officer_portal.py` – Backend & integration |

## File Structure

```
EcoSentinel/
├── app.py               ← Main entry point (Member 4)
├── citizen_portal.py    ← Citizen UI (Member 1)
├── data.py              ← CPCB data fetching (Member 2)
├── dashboard.py         ← Air quality charts (Member 2)
├── ai_analysis.py       ← AI incident analysis (Member 3)
├── compliance.py        ← Compliance checks (Member 3)
├── database.py          ← SQLite backend (Member 4)
├── officer_portal.py    ← Officer UI (Member 4)
├── requirements.txt
└── README.md
```

## Setup & Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application
streamlit run app.py
```

The SQLite database (`ecosentinel.db`) is created automatically on first run.

## Key Workflows

### Citizen
1. Open the **Citizen Portal** tab
2. Fill in the pollution complaint form
3. Submit → get a unique **ECO-XXXXXXXX** incident ID

### Environmental Officer
1. Open the **Officer Portal** tab
2. View all incidents with risk levels and statuses
3. Select an incident to see full details + AI analysis
4. Assign corrective actions and update status

## Integration Contracts

| Function | Module | Returns |
|----------|--------|---------|
| `show_citizen_portal()` | citizen_portal.py | `dict` or `None` |
| `get_air_quality(location)` | data.py | `pd.DataFrame` |
| `show_dashboard()` | dashboard.py | renders Streamlit UI |
| `analyse_incident(complaint, readings)` | ai_analysis.py | `dict` |
| `check_compliance(readings)` | compliance.py | `dict` |

## Database

SQLite file: `ecosentinel.db`

Tables: `incidents`, `actions`

Data is persistent across application restarts.

## Important Notes

- AI analysis is **decision support only**, not a legal determination.
- Citizen reports are separate from verified monitoring-station readings.
- Officer review is a required step before any enforcement action.

