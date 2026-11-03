from database import (
    init_db,
    save_complaint,
    get_all_complaints,
    get_complaint,
    save_analysis,
    update_status,
    save_action,
    get_actions
)

# 1. Initialize database
init_db()
print("Database initialized!")

# 2. Create sample complaint
complaint = {
    "type": "Smoke",
    "location": "Andheri, Mumbai",
    "description": "Thick black smoke coming from a nearby factory"
}

# 3. Save complaint
incident_id = save_complaint(complaint)
print("Incident saved:", incident_id)

# 4. Retrieve all complaints
incidents = get_all_complaints()
print("\nAll incidents:")
print(incidents)

# 5. Retrieve one complaint
incident = get_complaint(incident_id)
print("\nSelected incident:")
print(incident)

# 6. Save AI analysis
analysis = {
    "risk_level": "High",
    "summary": "Potential air pollution incident",
    "evidence": "Citizen reports thick black smoke",
    "recommendation": "Arrange a local inspection"
}

save_analysis(incident_id, analysis)
print("\nAnalysis saved!")

# 7. Update incident status
update_status(incident_id, "Under Investigation")
print("Status updated!")

# 8. Assign corrective action
save_action(
    incident_id,
    "Inspect the reported industrial location"
)

print("\nAssigned actions:")
print(get_actions(incident_id))

print("\nDATABASE TEST COMPLETED!")