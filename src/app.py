"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path
import os
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .models import Activity, User, Enrollment


app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=current_dir / "static"), name="static")


# Create DB tables
def init_db():
    Base.metadata.create_all(bind=engine)
    # Seed sample activities if none exist
    db = next(get_db())
    try:
        count = db.query(Activity).count()
        if count == 0:
            samples = [
                {
                    "name": "Chess Club",
                    "description": "Learn strategies and compete in chess tournaments",
                    "schedule": "Fridays, 3:30 PM - 5:00 PM",
                    "max_participants": 12,
                },
                {
                    "name": "Programming Class",
                    "description": "Learn programming fundamentals and build software projects",
                    "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
                    "max_participants": 20,
                },
                {
                    "name": "Gym Class",
                    "description": "Physical education and sports activities",
                    "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
                    "max_participants": 30,
                },
            ]
            for s in samples:
                a = Activity(**s)
                db.add(a)
            db.commit()
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


def activity_to_dict(db: Session, activity: Activity):
    participants = [e.user_email for e in activity.enrollments]
    return {
        "name": activity.name,
        "description": activity.description,
        "schedule": activity.schedule,
        "max_participants": activity.max_participants,
        "participants": participants,
    }


@app.get("/activities")
def get_activities(db: Session = Depends(get_db)):
    activities = db.query(Activity).all()
    return {a.name: activity_to_dict(db, a) for a in activities}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, db: Session = Depends(get_db)):
    # Validate activity exists
    activity = db.query(Activity).filter(Activity.name == activity_name).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Ensure user exists
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email)
        db.add(user)
        db.commit()

    # Validate not already enrolled
    enrolled = db.query(Enrollment).filter(Enrollment.activity_id == activity.id, Enrollment.user_email == email).first()
    if enrolled:
        raise HTTPException(status_code=400, detail="Student is already signed up")

    # Check capacity
    current = db.query(Enrollment).filter(Enrollment.activity_id == activity.id).count()
    if activity.max_participants and current >= activity.max_participants:
        raise HTTPException(status_code=400, detail="Activity is full")

    enrollment = Enrollment(activity_id=activity.id, user_email=email)
    db.add(enrollment)
    db.commit()
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, db: Session = Depends(get_db)):
    activity = db.query(Activity).filter(Activity.name == activity_name).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    enrollment = db.query(Enrollment).filter(Enrollment.activity_id == activity.id, Enrollment.user_email == email).first()
    if not enrollment:
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

    db.delete(enrollment)
    db.commit()
    return {"message": f"Unregistered {email} from {activity_name}"}
