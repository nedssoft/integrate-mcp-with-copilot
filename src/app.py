"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
import re
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Schedule parsing helpers

_DAY_NAMES = {
    "monday": "Monday", "mondays": "Monday",
    "tuesday": "Tuesday", "tuesdays": "Tuesday",
    "wednesday": "Wednesday", "wednesdays": "Wednesday",
    "thursday": "Thursday", "thursdays": "Thursday",
    "friday": "Friday", "fridays": "Friday",
    "saturday": "Saturday", "saturdays": "Saturday",
    "sunday": "Sunday", "sundays": "Sunday",
}


def _time_to_minutes(time_str: str) -> int:
    """Convert a time string like '3:30 PM' to minutes since midnight."""
    match = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)", time_str.strip(), re.IGNORECASE)
    if not match:
        return 0
    hours, minutes, period = int(match.group(1)), int(match.group(2)), match.group(3).upper()
    if period == "PM" and hours != 12:
        hours += 12
    elif period == "AM" and hours == 12:
        hours = 0
    return hours * 60 + minutes


def _parse_schedule(schedule: str) -> list[tuple[str, int, int]]:
    """Return a list of (day, start_minutes, end_minutes) tuples for a schedule string."""
    time_match = re.search(
        r"(\d{1,2}:\d{2}\s*(?:AM|PM))\s*-\s*(\d{1,2}:\d{2}\s*(?:AM|PM))$",
        schedule,
        re.IGNORECASE,
    )
    if not time_match:
        return []
    start = _time_to_minutes(time_match.group(1))
    end = _time_to_minutes(time_match.group(2))
    if end <= start:
        return []
    days_str = schedule[: time_match.start()].rstrip(", ")
    days = []
    for word in re.split(r"[\s,]+", days_str):
        day = _DAY_NAMES.get(word.lower())
        if day and day not in days:
            days.append(day)
    return [(day, start, end) for day in days]


def _schedules_overlap(schedule_a: str, schedule_b: str) -> bool:
    """Return True if two schedule strings share an overlapping day/time slot."""
    for day_a, start_a, end_a in _parse_schedule(schedule_a):
        for day_b, start_b, end_b in _parse_schedule(schedule_b):
            if day_a == day_b and start_a < end_b and start_b < end_a:
                return True
    return False


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

    # Check for schedule conflicts with existing enrollments
    for enrolled_name, enrolled_activity in activities.items():
        if enrolled_name == activity_name:
            continue
        if email in enrolled_activity["participants"]:
            if _schedules_overlap(activity["schedule"], enrolled_activity["schedule"]):
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"Schedule conflict: '{activity_name}' "
                        f"({activity['schedule']}) overlaps with "
                        f"'{enrolled_name}' ({enrolled_activity['schedule']})"
                    ),
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
