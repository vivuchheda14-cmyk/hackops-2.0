from database import (
    init_db,
    save_complaint,
    get_complaint,
    save_analysis
)

# Import your teammates' modules
from data import get_air_quality
from ai_analysis import analyse_incident

# Initialize database
init_db()

# Sample citizen complaint
complaint = {
    "type": "Smoke",
    "location": "Mumbai",
    "description": "Thick black smoke near an industrial area"
}

# Step 1: Save complaint FIRST
incident_id = save_complaint(complaint)

complaint["incident_id"] = incident_id

print("Complaint saved:", incident_id)

# Step 2: Fetch air quality readings
try:
    readings = get_air_quality(complaint["location"])
    print("Air quality readings retrieved:")
    print(readings)

except Exception as e:
    print("Air quality retrieval failed:", e)
    readings = None

# Step 3: Run AI analysis
try:
    analysis = analyse_incident(complaint, readings)

    print("\nAI Analysis:")
    print(analysis)

    save_analysis(incident_id, analysis)

except Exception as e:
    print("AI analysis failed:", e)

# Step 4: Verify database record
print("\nFinal saved incident:")
print(get_complaint(incident_id))