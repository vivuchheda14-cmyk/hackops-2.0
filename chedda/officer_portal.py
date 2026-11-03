"""
officer_portal.py – EcoSentinel Environmental Officer Portal
Member 4 responsibility: Officer Interface

Provides the officer-facing Streamlit UI for reviewing incidents,
assigning corrective actions and updating statuses.
"""

import json
import streamlit as st

from database import (
    get_all_complaints,
    get_complaint,
    get_actions,
    update_status,
    save_action,
)

# ─── Constants ────────────────────────────────────────────────────────────────

STATUS_OPTIONS  = ["Reported", "Under Investigation", "Resolved"]
ACTION_STATUSES = ["Pending", "In Progress", "Completed"]

RISK_COLORS = {
    "High":    "🔴",
    "Medium":  "🟡",
    "Low":     "🟢",
    "Unknown": "⚪",
}

STATUS_ICONS = {
    "Reported":            "📋",
    "Under Investigation": "🔍",
    "Resolved":            "✅",
}


# ─── Helper Functions ─────────────────────────────────────────────────────────

def _risk_badge(risk_level: str) -> str:
    icon = RISK_COLORS.get(risk_level, "⚪")
    return f"{icon} {risk_level}"


def _status_badge(status: str) -> str:
    icon = STATUS_ICONS.get(status, "📋")
    return f"{icon} {status}"


def _parse_analysis(raw_analysis) -> dict | None:
    """
    Safely parse the analysis field which is stored as a JSON string.
    Returns a dict or None.
    """
    if not raw_analysis:
        return None
    if isinstance(raw_analysis, dict):
        return raw_analysis
    try:
        return json.loads(raw_analysis)
    except (json.JSONDecodeError, TypeError):
        return {"raw": str(raw_analysis)}


# ─── Metric Row ───────────────────────────────────────────────────────────────

def _show_metrics(complaints: list[dict]):
    """Display four summary metric cards at the top of the portal."""
    total            = len(complaints)
    high_risk        = sum(1 for c in complaints if c.get("risk_level") == "High")
    under_invest     = sum(1 for c in complaints if c.get("status") == "Under Investigation")
    resolved         = sum(1 for c in complaints if c.get("status") == "Resolved")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📊 Total Incidents",          total)
    col2.metric("🔴 High-Risk Incidents",       high_risk)
    col3.metric("🔍 Under Investigation",       under_invest)
    col4.metric("✅ Resolved",                  resolved)


# ─── Incident List Panel ──────────────────────────────────────────────────────

def _show_incident_list(complaints: list[dict]) -> str | None:
    """
    Display every incident in a compact table and return the incident_id
    that the officer has selected, or None.
    """
    st.subheader("📋 All Incidents")

    if not complaints:
        st.info("No incidents have been reported yet.")
        return None

    # Build a display table
    import pandas as pd

    rows = []
    for c in complaints:
        rows.append({
            "Incident ID":  c.get("incident_id", "—"),
            "Type":         c.get("issue_type",  "—"),
            "Location":     c.get("location",    "—"),
            "Priority":     c.get("priority",    "—"),
            "Risk Level":   _risk_badge(c.get("risk_level", "Unknown")),
            "Status":       _status_badge(c.get("status", "Reported")),
            "Submitted":    c.get("timestamp",   "—")[:19].replace("T", " "),
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Selectbox to pick an incident for detail view
    incident_ids = [c["incident_id"] for c in complaints]
    selected = st.selectbox(
        "Select an incident to review:",
        options=["— Select —"] + incident_ids,
        key="officer_selected_incident",
    )
    return selected if selected != "— Select —" else None


# ─── Incident Detail Panel ────────────────────────────────────────────────────

def _show_incident_detail(incident_id: str):
    """Render the full detail view for a selected incident."""
    complaint = get_complaint(incident_id)
    if not complaint:
        st.error(f"Incident {incident_id} could not be found in the database.")
        return

    st.markdown("---")
    st.subheader(f"🗂️ Incident: {incident_id}")

    # ── 1. Citizen Complaint ──────────────────────────────────────────────────
    with st.expander("📝 Original Citizen Complaint", expanded=True):
        col_a, col_b = st.columns(2)
        col_a.markdown(f"**Issue Type:** {complaint.get('issue_type', '—')}")
        col_a.markdown(f"**Location:** {complaint.get('location', '—')}")
        col_a.markdown(f"**Priority:** {complaint.get('priority', '—')}")
        col_b.markdown(f"**Submitted:** {complaint.get('timestamp', '—')[:19].replace('T', ' ')} UTC")
        col_b.markdown(f"**Current Status:** {_status_badge(complaint.get('status', 'Reported'))}")
        col_b.markdown(f"**Risk Level:** {_risk_badge(complaint.get('risk_level', 'Unknown'))}")
        st.markdown("**Description:**")
        st.info(complaint.get("description", "No description provided."))

        if complaint.get("evidence"):
            st.markdown(f"**Evidence:** `{complaint['evidence']}`")

    # ── 2. AI Analysis ────────────────────────────────────────────────────────
    with st.expander("🤖 AI Analysis & Environmental Assessment", expanded=True):
        analysis = _parse_analysis(complaint.get("analysis"))

        if not analysis:
            st.warning(
                "AI analysis has not been completed yet for this incident. "
                "The officer may review the complaint manually."
            )
        else:
            # Disclaimer
            st.caption(
                "⚠️ The following is AI-generated decision support. "
                "It is NOT an official government determination or legally verified finding."
            )

            # Handle nested structure from ai_analysis.py (Member 3)
            # Support both flat dict and nested {"analysis": {...}} structures
            if "analysis" in analysis and isinstance(analysis["analysis"], dict):
                inner = analysis["analysis"]
            else:
                inner = analysis

            risk = inner.get("risk_level", analysis.get("risk_level", "Unknown"))
            st.markdown(f"**AI Risk Assessment:** {_risk_badge(risk)}")

            summary = inner.get("summary", analysis.get("summary", ""))
            if summary:
                st.markdown("**Summary:**")
                st.write(summary)

            evidence = inner.get("evidence", analysis.get("evidence", ""))
            if evidence:
                st.markdown("**Supporting Evidence:**")
                st.write(evidence)

            recommendation = inner.get("recommendation", analysis.get("recommendation", ""))
            if recommendation:
                st.markdown("**Recommended Action:**")
                st.success(recommendation)

            # Show raw JSON in a collapsed expander for transparency
            with st.expander("🔍 Full Analysis JSON (raw)"):
                st.json(analysis)

    # ── 3. Compliance Assessment ──────────────────────────────────────────────
    # This data may be included in the analysis dict by Member 3
    with st.expander("📜 Compliance Assessment", expanded=False):
        analysis = _parse_analysis(complaint.get("analysis"))
        compliance_data = None
        if analysis:
            compliance_data = analysis.get("compliance") or analysis.get("compliance_check")

        if compliance_data:
            st.caption(
                "⚠️ Compliance notes are AI-generated based on available data. "
                "Official enforcement requires regulatory verification."
            )
            if isinstance(compliance_data, dict):
                for key, val in compliance_data.items():
                    st.markdown(f"**{key.replace('_', ' ').title()}:** {val}")
            else:
                st.write(compliance_data)
        else:
            st.info("No compliance assessment is available for this incident yet.")

    # ── 4. Existing Corrective Actions ────────────────────────────────────────
    with st.expander("🛠️ Assigned Corrective Actions", expanded=True):
        actions = get_actions(incident_id)
        if not actions:
            st.info("No corrective actions have been assigned yet.")
        else:
            for act in actions:
                act_col1, act_col2 = st.columns([3, 1])
                act_col1.markdown(
                    f"**{act.get('assigned_to', '—')}** — {act.get('action', '—')}"
                )
                act_status = act.get("status", "Pending")
                act_col2.markdown(f"`{act_status}`")
                st.caption(f"Logged at {act.get('created_at', '—')[:19].replace('T', ' ')} UTC")
                st.markdown("---")

    # ── 5. Status Management ──────────────────────────────────────────────────
    st.markdown("### 🔄 Update Incident Status")
    current_status = complaint.get("status", "Reported")
    try:
        default_index = STATUS_OPTIONS.index(current_status)
    except ValueError:
        default_index = 0

    new_status = st.selectbox(
        "Set status:",
        options=STATUS_OPTIONS,
        index=default_index,
        key=f"status_select_{incident_id}",
    )

    if st.button("✅ Update Status", key=f"update_status_btn_{incident_id}"):
        if new_status == current_status:
            st.info(f"Status is already set to '{current_status}'. No change made.")
        else:
            success = update_status(incident_id, new_status)
            if success:
                st.success(f"Status updated to **{new_status}**.")
                st.rerun()
            else:
                st.error("Failed to update status. Please try again.")

    st.markdown("---")

    # ── 6. Assign Corrective Action ───────────────────────────────────────────
    st.markdown("### 📝 Assign Corrective Action")

    with st.form(key=f"action_form_{incident_id}"):
        officer_name = st.text_input(
            "Officer Name",
            placeholder="e.g. Inspector Sharma",
            key=f"officer_name_{incident_id}",
        )
        action_description = st.text_area(
            "Corrective Action",
            placeholder="Describe the action to be taken...",
            height=100,
            key=f"action_desc_{incident_id}",
        )
        action_status = st.selectbox(
            "Action Status",
            options=ACTION_STATUSES,
            key=f"action_status_{incident_id}",
        )
        submitted = st.form_submit_button("📌 Assign Action")

    if submitted:
        if not officer_name.strip():
            st.error("Please enter the officer name.")
        elif not action_description.strip():
            st.error("Please enter the corrective action description.")
        else:
            action_payload = {
                "assigned_to": officer_name.strip(),
                "action":      action_description.strip(),
                "status":      action_status,
            }
            success = save_action(incident_id, action_payload)
            if success:
                st.success(
                    f"Action assigned to **{officer_name}** and saved successfully."
                )
                st.rerun()
            else:
                st.error("Failed to save the corrective action. Please try again.")


# ─── Main Entry Point ─────────────────────────────────────────────────────────

def show_officer_portal():
    """
    Render the complete Environmental Officer Portal.
    Called by app.py when the Officer Portal page is selected.
    """
    st.title("🏛️ Environmental Officer Portal")
    st.caption(
        "Review citizen complaints, examine AI-generated environmental assessments, "
        "assign corrective actions and track incident resolution."
    )

    # Load all complaints fresh on every render
    complaints = get_all_complaints()

    # ── Top metrics ──
    _show_metrics(complaints)

    st.markdown("---")

    # ── Incident list + selector ──
    selected_id = _show_incident_list(complaints)

    # ── Incident detail ──
    if selected_id:
        _show_incident_detail(selected_id)
    else:
        if complaints:
            st.info("👆 Select an incident from the list above to review its details.")

