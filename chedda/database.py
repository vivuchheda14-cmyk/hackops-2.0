"""
database.py – EcoSentinel SQLite Database Layer
Member 4 responsibility: Backend Database Manager

This module handles all data persistence for EcoSentinel.
It uses SQLite so no separate database server is required.
"""

import sqlite3
import json
import uuid
from datetime import datetime, timezone


# ─── Configuration ────────────────────────────────────────────────────────────

DB_FILE = "ecosentinel.db"

ALLOWED_STATUSES = {"Reported", "Under Investigation", "Resolved"}
ALLOWED_ACTION_STATUSES = {"Pending", "In Progress", "Completed"}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_connection():
    """
    Open and return a SQLite connection with row_factory set so that
    rows behave like dictionaries (column-name access).
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row          # allows row["column_name"]
    conn.execute("PRAGMA journal_mode=WAL") # safer for concurrent reads
    return conn


def _generate_incident_id():
    """
    Generate a short, collision-safe incident ID in the format ECO-XXXXXXXX.
    Uses the first 8 hex characters of a UUID4.
    """
    return "ECO-" + uuid.uuid4().hex[:8].upper()


def _now_iso():
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _row_to_dict(row):
    """Convert a sqlite3.Row object to a plain Python dictionary."""
    return dict(row) if row else None


# ─── 1. Initialise Database ───────────────────────────────────────────────────

def init_db():
    """
    Create the database tables if they do not already exist.
    Safe to call every time the application starts (uses IF NOT EXISTS).
    """
    conn = _get_connection()
    try:
        cursor = conn.cursor()

        # ── incidents table ──
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                incident_id  TEXT PRIMARY KEY,
                issue_type   TEXT NOT NULL,
                location     TEXT NOT NULL,
                description  TEXT NOT NULL,
                timestamp    TEXT NOT NULL,
                priority     TEXT DEFAULT 'Medium',
                risk_level   TEXT DEFAULT 'Unknown',
                status       TEXT DEFAULT 'Reported',
                analysis     TEXT DEFAULT NULL,
                evidence     TEXT DEFAULT NULL
            )
        """)

        # ── actions table ──
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS actions (
                action_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id  TEXT NOT NULL,
                assigned_to  TEXT NOT NULL,
                action       TEXT NOT NULL,
                status       TEXT DEFAULT 'Pending',
                created_at   TEXT NOT NULL,
                FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
            )
        """)

        conn.commit()
        print("[DB] Database initialised successfully.")
    except sqlite3.Error as e:
        print(f"[DB ERROR] Failed to initialise database: {e}")
    finally:
        conn.close()


# ─── 2. Save a Citizen Complaint ─────────────────────────────────────────────

def save_complaint(complaint: dict) -> str:
    """
    Persist a new citizen complaint and return its unique incident ID.

    Expected complaint keys:
        type        – Issue type (Smoke / Dust / Gas / Odour / Other)
        location    – Reported location string
        description – Citizen's complaint text
        priority    – (optional) Preliminary priority
        evidence    – (optional) Evidence filename or reference

    Returns the generated incident_id string (e.g. "ECO-3F9A1B2C").
    """
    incident_id = _generate_incident_id()
    timestamp   = _now_iso()

    conn = _get_connection()
    try:
        conn.execute(
            """
            INSERT INTO incidents
                (incident_id, issue_type, location, description,
                 timestamp, priority, evidence)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                incident_id,
                complaint.get("type", "Other"),
                complaint.get("location", "Unknown"),
                complaint.get("description", ""),
                timestamp,
                complaint.get("priority", "Medium"),
                complaint.get("evidence", None),
            ),
        )
        conn.commit()
        print(f"[DB] Complaint saved: {incident_id}")
        return incident_id
    except sqlite3.Error as e:
        print(f"[DB ERROR] Failed to save complaint: {e}")
        # Return the generated ID even on error so the caller can handle it
        return incident_id
    finally:
        conn.close()


# ─── 3. Retrieve All Complaints ───────────────────────────────────────────────

def get_all_complaints() -> list[dict]:
    """
    Return all incidents as a list of dictionaries, newest first.
    Returns an empty list if there are no incidents or on error.
    """
    conn = _get_connection()
    try:
        cursor = conn.execute(
            "SELECT * FROM incidents ORDER BY timestamp DESC"
        )
        rows = cursor.fetchall()
        return [_row_to_dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"[DB ERROR] Failed to retrieve complaints: {e}")
        return []
    finally:
        conn.close()


# ─── 4. Retrieve One Complaint ────────────────────────────────────────────────

def get_complaint(incident_id: str) -> dict | None:
    """
    Return one incident as a dictionary, or None if not found.
    """
    conn = _get_connection()
    try:
        cursor = conn.execute(
            "SELECT * FROM incidents WHERE incident_id = ?",
            (incident_id,),
        )
        row = cursor.fetchone()
        return _row_to_dict(row)
    except sqlite3.Error as e:
        print(f"[DB ERROR] Failed to retrieve incident {incident_id}: {e}")
        return None
    finally:
        conn.close()


# ─── 5. Save AI Analysis ──────────────────────────────────────────────────────

def save_analysis(incident_id: str, analysis: dict) -> bool:
    """
    Persist AI analysis for an incident.

    The analysis dictionary is serialised to JSON and stored in the
    'analysis' column.  The 'risk_level' column is also updated if
    the analysis contains a 'risk_level' key.

    Returns True on success, False on failure.
    """
    serialisation_ok = True
    try:
        analysis_json = json.dumps(analysis)
    except (TypeError, ValueError) as e:
        print(f"[DB ERROR] Could not serialise analysis to JSON: {e}")
        analysis_json = json.dumps({"error": "Analysis could not be serialised"})
        serialisation_ok = False

    # Only update risk_level when the analysis was fully serialisable.
    # If serialisation failed we keep whatever risk_level is already stored
    # so a bad analysis dict cannot silently overwrite a good one.
    if serialisation_ok and isinstance(analysis, dict):
        risk_level = analysis.get("risk_level", "Unknown")
    else:
        risk_level = None   # sentinel – handled in the SQL below

    conn = _get_connection()
    try:
        if risk_level is not None:
            conn.execute(
                """
                UPDATE incidents
                   SET analysis   = ?,
                       risk_level = ?
                 WHERE incident_id = ?
                """,
                (analysis_json, risk_level, incident_id),
            )
        else:
            # Serialisation failed – only update the analysis text, not risk_level
            conn.execute(
                """
                UPDATE incidents
                   SET analysis = ?
                 WHERE incident_id = ?
                """,
                (analysis_json, incident_id),
            )
        conn.commit()
        print(f"[DB] Analysis saved for {incident_id}")
        return True
    except sqlite3.Error as e:
        print(f"[DB ERROR] Failed to save analysis for {incident_id}: {e}")
        return False
    finally:
        conn.close()


# ─── 6. Update Incident Status ────────────────────────────────────────────────

def update_status(incident_id: str, status: str) -> bool:
    """
    Update the status of an incident.

    Allowed values: 'Reported', 'Under Investigation', 'Resolved'.
    Returns True on success, False if the status is invalid or on error.
    """
    if status not in ALLOWED_STATUSES:
        print(f"[DB ERROR] Invalid status '{status}'. Must be one of {ALLOWED_STATUSES}")
        return False

    conn = _get_connection()
    try:
        conn.execute(
            "UPDATE incidents SET status = ? WHERE incident_id = ?",
            (status, incident_id),
        )
        conn.commit()
        print(f"[DB] Status updated for {incident_id} → {status}")
        return True
    except sqlite3.Error as e:
        print(f"[DB ERROR] Failed to update status for {incident_id}: {e}")
        return False
    finally:
        conn.close()


# ─── 7. Save Corrective Action ────────────────────────────────────────────────

def save_action(incident_id: str, action: dict) -> bool:
    """
    Save an officer-assigned corrective action for an incident.

    Expected action keys:
        assigned_to – Officer name
        action      – Action description
        status      – (optional) 'Pending' | 'In Progress' | 'Completed'

    Returns True on success, False on failure.
    """
    conn = _get_connection()
    try:
        conn.execute(
            """
            INSERT INTO actions
                (incident_id, assigned_to, action, status, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                incident_id,
                action.get("assigned_to", "Unknown Officer"),
                action.get("action", ""),
                action.get("status", "Pending"),
                _now_iso(),
            ),
        )
        conn.commit()
        print(f"[DB] Action saved for {incident_id}")
        return True
    except sqlite3.Error as e:
        print(f"[DB ERROR] Failed to save action for {incident_id}: {e}")
        return False
    finally:
        conn.close()


# ─── 8. Retrieve Corrective Actions ──────────────────────────────────────────

def get_actions(incident_id: str) -> list[dict]:
    """
    Return all corrective actions for an incident, newest first.
    Returns an empty list if none exist or on error.
    """
    conn = _get_connection()
    try:
        cursor = conn.execute(
            """
            SELECT * FROM actions
             WHERE incident_id = ?
             ORDER BY created_at DESC
            """,
            (incident_id,),
        )
        rows = cursor.fetchall()
        return [_row_to_dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"[DB ERROR] Failed to retrieve actions for {incident_id}: {e}")
        return []
    finally:
        conn.close()


# ─── Quick Self-Test (run this file directly to verify) ───────────────────────

if __name__ == "__main__":
    print("=== EcoSentinel Database Self-Test ===")
    init_db()

    # Test complaint
    test_complaint = {
        "type": "Smoke",
        "location": "Mumbai – Andheri East",
        "description": "Thick black smoke rising from an industrial shed near the highway.",
        "priority": "High",
    }
    iid = save_complaint(test_complaint)
    print(f"Saved complaint: {iid}")

    # Test retrieval
    record = get_complaint(iid)
    print(f"Retrieved: {record}")

    # Test analysis
    test_analysis = {
        "risk_level": "High",
        "summary": "Elevated smoke detected near industrial zone.",
        "evidence": "PM2.5 readings above safe threshold at nearby station.",
        "recommendation": "Dispatch field inspector within 24 hours.",
    }
    save_analysis(iid, test_analysis)

    # Test status update
    update_status(iid, "Under Investigation")

    # Test action
    test_action = {
        "assigned_to": "Inspector Sharma",
        "action": "Conduct site inspection and collect air samples.",
        "status": "Pending",
    }
    save_action(iid, test_action)

    # Verify actions
    actions = get_actions(iid)
    print(f"Actions: {actions}")

    all_complaints = get_all_complaints()
    print(f"Total complaints in DB: {len(all_complaints)}")
    print("=== Self-Test Complete ===")

