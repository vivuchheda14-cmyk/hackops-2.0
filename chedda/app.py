"""
app.py – EcoSentinel Main Application Entry Point
Member 4 responsibility: Application Integration

This is the single entry point for the entire EcoSentinel application.
Run with:  streamlit run app.py

Architecture:
  ┌─────────────────────────────────────────────┐
  │                   app.py                    │
  │  ┌──────────────┐  ┌──────────────────────┐ │
  │  │citizen_portal│  │ officer_portal       │ │
  │  │  (Member 1)  │  │   (Member 4 – ME)    │ │
  │  └──────┬───────┘  └──────────────────────┘ │
  │         │ complaint                          │
  │  ┌──────▼───────┐  ┌──────────────────────┐ │
  │  │  database.py │  │  dashboard.py        │ │
  │  │  (Member 4)  │  │   (Member 2)         │ │
  │  └──────┬───────┘  └──────────────────────┘ │
  │         │ incident_id                        │
  │  ┌──────▼───────┐  ┌──────────────────────┐ │
  │  │   data.py    │  │  compliance.py       │ │
  │  │  (Member 2)  │  │   (Member 3)         │ │
  │  └──────┬───────┘  └──────────────────────┘ │
  │         │ readings                           │
  │  ┌──────▼───────┐                            │
  │  │ ai_analysis  │                            │
  │  │  (Member 3)  │                            │
  │  └──────────────┘                            │
  └─────────────────────────────────────────────┘
"""

import streamlit as st

# ─── Page configuration (must be the very first Streamlit call) ───────────────
st.set_page_config(
    page_title="EcoSentinel – Air Pollution Monitor",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Database initialisation ──────────────────────────────────────────────────
# Import and call init_db() immediately so the DB is always ready.
from database import (
    init_db,
    save_complaint,
    save_analysis,
    get_all_complaints,
)

init_db()

# ─── Graceful teammate module imports ─────────────────────────────────────────
# Each import is wrapped in try/except so the app continues to work even if a
# teammate's file is not yet complete.  A stub is substituted when needed.
# DO NOT modify these stubs into full implementations – they are placeholders
# only, and will be replaced once the real teammate code is committed.

# ── Member 1 – citizen_portal.py ─────────────────────────────────────────────
try:
    from citizen_portal import show_citizen_portal
    _citizen_portal_available = True
except ImportError as _e:
    _citizen_portal_available = False
    def show_citizen_portal():
        """Fallback stub – Member 1 citizen_portal.py not yet available."""
        st.warning(
            "⚠️ **Citizen portal module not yet available.**  "
            "Waiting for Member 1 to commit `citizen_portal.py`."
        )
        st.markdown("### 📝 Temporary Complaint Form (Integration Fallback)")
        st.caption(
            "This is a temporary form used only until the real citizen portal is ready. "
            "It follows the agreed interface and will be replaced automatically."
        )
        with st.form("fallback_complaint_form"):
            issue_type  = st.selectbox(
                "Issue Type",
                ["Smoke", "Dust", "Gas", "Odour", "Other"],
                key="fb_type",
            )
            location    = st.text_input("Location",    placeholder="e.g. Mumbai – Andheri East", key="fb_loc")
            description = st.text_area("Description", placeholder="Describe what you observed...", key="fb_desc")
            priority    = st.selectbox("Priority", ["Low", "Medium", "High"], index=1, key="fb_priority")
            submitted   = st.form_submit_button("🚨 Submit Report")

        if submitted:
            if not location.strip() or not description.strip():
                st.error("Please fill in the location and description.")
                return None
            return {
                "type":        issue_type,
                "location":    location.strip(),
                "description": description.strip(),
                "priority":    priority,
            }
        return None

# ── Member 2 – data.py ───────────────────────────────────────────────────────
try:
    from data import get_air_quality
    _data_available = True
except ImportError:
    _data_available = False
    import pandas as pd
    def get_air_quality(location: str):
        """Fallback stub – Member 2 data.py not yet available."""
        st.info(
            f"📡 Air-quality module (`data.py`) is not yet available. "
            f"Environmental readings for **{location}** could not be retrieved."
        )
        return pd.DataFrame()   # Empty DataFrame – safe for ai_analysis

# ── Member 2 – dashboard.py ──────────────────────────────────────────────────
try:
    from dashboard import show_dashboard
    _dashboard_available = True
except ImportError:
    _dashboard_available = False
    def show_dashboard():
        """Fallback stub – Member 2 dashboard.py not yet available."""
        st.warning(
            "⚠️ **Air Quality Dashboard** is not yet available.  "
            "Waiting for Member 2 to commit `dashboard.py`."
        )
        st.info(
            "Once `dashboard.py` is ready this page will display real-time "
            "CPCB/data.gov.in air-quality readings and charts."
        )

# ── Member 3 – ai_analysis.py ────────────────────────────────────────────────
try:
    from ai_analysis import analyse_incident
    _ai_available = True
except ImportError:
    _ai_available = False
    def analyse_incident(complaint, readings):
        """Fallback stub – Member 3 ai_analysis.py not yet available."""
        return {
            "risk_level":     "Unknown",
            "summary":        "AI analysis module is not yet available.",
            "evidence":       "No readings could be processed.",
            "recommendation": "Please review the complaint manually.",
        }

# ── Member 3 – compliance.py ─────────────────────────────────────────────────
try:
    from compliance import check_compliance
    _compliance_available = True
except ImportError:
    _compliance_available = False
    def check_compliance(readings):
        """Fallback stub – Member 3 compliance.py not yet available."""
        return {"status": "Compliance module not yet available."}

# ── Member 4 – officer_portal.py ─────────────────────────────────────────────
from officer_portal import show_officer_portal


# ─── Sidebar Navigation ───────────────────────────────────────────────────────

def _sidebar():
    with st.sidebar:
        st.image(
            "https://img.icons8.com/color/96/plant-under-rain.png",
            width=80,
        )
        st.title("🌿 EcoSentinel")
        st.caption("AI-Powered Air Pollution Monitor")
        st.markdown("---")

        page = st.radio(
            "Navigation",
            options=[
                "🏠 Citizen Portal",
                "📊 Air Quality Dashboard",
                "🏛️ Officer Portal",
            ],
            key="nav_page",
        )

        st.markdown("---")
        st.caption("**Module Status**")

        def _status_dot(available: bool) -> str:
            return "🟢" if available else "🔴"

        st.caption(f"{_status_dot(_citizen_portal_available)} citizen_portal.py  (M1)")
        st.caption(f"{_status_dot(_data_available)} data.py  (M2)")
        st.caption(f"{_status_dot(_dashboard_available)} dashboard.py  (M2)")
        st.caption(f"{_status_dot(_ai_available)} ai_analysis.py  (M3)")
        st.caption(f"{_status_dot(_compliance_available)} compliance.py  (M3)")
        st.caption("🟢 database.py  (M4)")
        st.caption("🟢 officer_portal.py  (M4)")

        # Show live incident count
        complaints = get_all_complaints()
        st.markdown("---")
        st.metric("Total Incidents", len(complaints))

    return page


# ─── Complaint Processing Pipeline ────────────────────────────────────────────

def _process_new_complaint(complaint: dict):
    """
    Execute the full citizen-to-database pipeline for a new complaint.

    This function is called ONCE per form submission.
    Streamlit session state is used to prevent duplicate processing on reruns.

    Pipeline:
      1. Save complaint → get incident_id   (always happens – never lost)
      2. Fetch air-quality readings          (may fail gracefully)
      3. Run AI analysis                     (may fail gracefully)
      4. Run compliance check                (may fail gracefully)
      5. Save combined analysis              (always attempted)
      6. Show confirmation with incident_id
    """

    # ── STEP 1: Save complaint to database ────────────────────────────────────
    # This must succeed before we attempt any external services.
    try:
        incident_id = save_complaint(complaint)
    except Exception as e:
        st.error(f"❌ Failed to save complaint: {e}")
        return

    # Store in session state so the confirmation persists across reruns
    st.session_state["last_incident_id"] = incident_id
    st.session_state["last_complaint"]   = complaint

    st.success(
        f"✅ Complaint submitted successfully!  "
        f"Your incident ID is **{incident_id}**. "
        f"Please keep this for your records."
    )

    # ── STEP 2: Retrieve air-quality readings ─────────────────────────────────
    readings = None
    try:
        with st.spinner("📡 Fetching air-quality data…"):
            readings = get_air_quality(complaint["location"])
    except Exception as e:
        st.warning(
            f"⚠️ Could not retrieve air-quality data for **{complaint['location']}**: {e}  \n"
            "Your complaint has been saved and is available for officer review."
        )
        import pandas as pd
        readings = pd.DataFrame()

    # ── STEP 3: AI Analysis ───────────────────────────────────────────────────
    analysis = {}
    try:
        with st.spinner("🤖 Running AI analysis…"):
            analysis = analyse_incident(complaint, readings)
    except Exception as e:
        st.warning(
            f"⚠️ AI analysis could not be completed: {e}  \n"
            "The incident is saved and an officer can review it manually."
        )
        analysis = {
            "risk_level":     "Unknown",
            "summary":        f"AI analysis failed: {e}",
            "evidence":       "Analysis unavailable – please review manually.",
            "recommendation": "Manual officer inspection recommended.",
        }

    # ── STEP 4: Compliance Check ──────────────────────────────────────────────
    try:
        if readings is not None and not (hasattr(readings, "empty") and readings.empty):
            compliance_result = check_compliance(readings)
            # Merge compliance result into analysis dict for storage
            if isinstance(compliance_result, dict):
                analysis["compliance"] = compliance_result
    except Exception as e:
        st.warning(f"⚠️ Compliance check could not be completed: {e}")

    # ── STEP 5: Save analysis to database ────────────────────────────────────
    try:
        save_analysis(incident_id, analysis)
    except Exception as e:
        st.warning(
            f"⚠️ Could not save AI analysis for {incident_id}: {e}  \n"
            "The complaint is stored. Analysis can be added later."
        )

    # ── STEP 6: Summary to citizen ────────────────────────────────────────────
    risk_level = analysis.get("risk_level", "Unknown") if analysis else "Unknown"

    with st.container(border=True):
        st.markdown(f"### 📋 Incident Summary — `{incident_id}`")
        col1, col2, col3 = st.columns(3)
        col1.metric("Issue Type",  complaint.get("type", "—"))
        col2.metric("Location",    complaint.get("location", "—"))
        col3.metric("Risk Level",  risk_level)

        if analysis.get("summary"):
            st.markdown("**AI Summary:**")
            st.info(analysis["summary"])

        if analysis.get("recommendation"):
            st.markdown("**Recommended Action:**")
            st.success(analysis["recommendation"])

        st.caption(
            "⚠️ The risk assessment above is AI-generated decision support. "
            "It is not an official environmental determination."
        )

    st.balloons()


# ─── Citizen Portal Page ──────────────────────────────────────────────────────

def _page_citizen_portal():
    st.title("🏠 Citizen Pollution Report")
    st.markdown(
        "Use this form to report a pollution incident in your area.  "
        "Your complaint will be reviewed by a qualified environmental officer."
    )
    st.markdown("---")

    # Show confirmation if a previous complaint was submitted this session
    if st.session_state.get("last_incident_id"):
        last_id = st.session_state["last_incident_id"]
        st.info(
            f"📌 Your latest incident ID this session: **{last_id}**  \n"
            "Submit a new complaint below or visit the Officer Portal to track progress."
        )

    # Call the citizen portal module (Member 1 or fallback)
    complaint = show_citizen_portal()

    # Only process if the form returned a complaint AND we haven't already
    # processed this exact submission (prevents duplicate creation on reruns).
    if complaint is not None:
        # Use a hash of the complaint to detect duplicates within the session.
        complaint_key = str(sorted(complaint.items()))
        already_processed_key = f"processed_{complaint_key}"

        if not st.session_state.get(already_processed_key, False):
            st.session_state[already_processed_key] = True
            _process_new_complaint(complaint)
        else:
            # The app reran but no new submission was made – show confirmation
            last_id = st.session_state.get("last_incident_id", "unknown")
            st.success(
                f"✅ Your complaint is already recorded under **{last_id}**.  "
                "Submit a new form to report another incident."
            )


# ─── Dashboard Page ───────────────────────────────────────────────────────────

def _page_dashboard():
    st.title("📊 Air Quality Dashboard")
    show_dashboard()


# ─── Officer Portal Page ──────────────────────────────────────────────────────

def _page_officer_portal():
    show_officer_portal()


# ─── Application Router ───────────────────────────────────────────────────────

def main():
    # Initialise session state keys if not present
    if "last_incident_id" not in st.session_state:
        st.session_state["last_incident_id"] = None
    if "last_complaint" not in st.session_state:
        st.session_state["last_complaint"] = None

    page = _sidebar()

    if "Citizen Portal" in page:
        _page_citizen_portal()
    elif "Dashboard" in page:
        _page_dashboard()
    elif "Officer Portal" in page:
        _page_officer_portal()


if __name__ == "__main__":
    main()

