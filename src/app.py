"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
import json
from pathlib import Path
from typing import Literal

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(current_dir, "static")), name="static")

# Authorized users who can mark/edit attendance
AUTHORIZED_USERS = {
    "coach@mergington.edu",
    "admin@mergington.edu"
}

# File path for persisting attendance records
ATTENDANCE_FILE = current_dir / "attendance.json"


def load_attendance() -> dict:
    """Load attendance records from file, returning empty dict if file doesn't exist."""
    if ATTENDANCE_FILE.exists():
        with open(ATTENDANCE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_attendance(data: dict) -> None:
    """Persist attendance records to file."""
    with open(ATTENDANCE_FILE, "w") as f:
        json.dump(data, f, indent=2)


# Attendance records structure: { activity_name: { date: { email: status } } }
attendance_records = load_attendance()

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}


@app.post("/activities/{activity_name}/attendance")
def mark_attendance(
    activity_name: str,
    email: str,
    date: str,
    status: Literal["present", "absent"],
    marked_by: str
):
    """Mark a student's attendance for an activity session (coaches/admin only)"""
    if marked_by not in AUTHORIZED_USERS:
        raise HTTPException(status_code=403, detail="Not authorized to mark attendance")

    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    if email not in activities[activity_name]["participants"]:
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

    attendance_records.setdefault(activity_name, {}).setdefault(date, {})[email] = status
    save_attendance(attendance_records)
    return {"message": f"Marked {email} as {status} for {activity_name} on {date}"}


@app.put("/activities/{activity_name}/attendance")
def edit_attendance(
    activity_name: str,
    email: str,
    date: str,
    status: Literal["present", "absent"],
    marked_by: str
):
    """Edit a student's attendance record for an activity session (coaches/admin only)"""
    if marked_by not in AUTHORIZED_USERS:
        raise HTTPException(status_code=403, detail="Not authorized to edit attendance")

    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    if (
        activity_name not in attendance_records
        or date not in attendance_records[activity_name]
        or email not in attendance_records[activity_name][date]
    ):
        raise HTTPException(status_code=404, detail="Attendance record not found")

    attendance_records[activity_name][date][email] = status
    save_attendance(attendance_records)
    return {"message": f"Updated {email} attendance to {status} for {activity_name} on {date}"}


@app.get("/activities/{activity_name}/attendance")
def get_activity_attendance(activity_name: str, date: str = None):
    """Get attendance summary for an activity, optionally filtered by date"""
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity_data = attendance_records.get(activity_name, {})

    if date:
        session = activity_data.get(date, {})
        present = [e for e, s in session.items() if s == "present"]
        absent = [e for e, s in session.items() if s == "absent"]
        return {
            "activity": activity_name,
            "date": date,
            "present": present,
            "absent": absent,
            "present_count": len(present),
            "absent_count": len(absent),
        }

    summary = []
    for session_date, records in sorted(activity_data.items()):
        present = [e for e, s in records.items() if s == "present"]
        absent = [e for e, s in records.items() if s == "absent"]
        summary.append({
            "date": session_date,
            "present": present,
            "absent": absent,
            "present_count": len(present),
            "absent_count": len(absent),
        })
    return {"activity": activity_name, "sessions": summary}


@app.get("/students/{email}/attendance")
def get_student_attendance(email: str):
    """Get a student's personal attendance history and percentage across all activities"""
    records = []
    total = 0
    present_count = 0

    for activity_name, sessions in attendance_records.items():
        for date, entries in sessions.items():
            if email in entries:
                status = entries[email]
                records.append({"activity": activity_name, "date": date, "status": status})
                total += 1
                if status == "present":
                    present_count += 1

    attendance_percentage = round((present_count / total) * 100, 1) if total > 0 else None

    return {
        "email": email,
        "records": sorted(records, key=lambda r: (r["date"], r["activity"])),
        "total_sessions": total,
        "present_count": present_count,
        "absent_count": total - present_count,
        "attendance_percentage": attendance_percentage,
    }
