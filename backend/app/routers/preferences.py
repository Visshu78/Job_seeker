from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, JobPreferences
from app.schemas import JobPreferencesOut, JobPreferencesUpdate
from app.routers.deps import get_current_user

router = APIRouter(prefix="/preferences", tags=["Job Preferences"])

@router.get("", response_model=JobPreferencesOut)
def get_preferences(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    prefs = db.query(JobPreferences).filter(JobPreferences.user_id == current_user.id).first()
    if not prefs:
        prefs = JobPreferences(
            user_id=current_user.id,
            preferred_roles=["AI Engineer", "Machine Learning Engineer", "Computer Vision Engineer", "Software Engineer"],
            employment_types=["Internship", "Full-time"],
            experience_levels=["Fresher", "0-1 years"],
            locations=["Bangalore", "Hyderabad", "Remote", "Pune"],
            remote_only=False,
            min_stipend=25000.0,
            min_salary=600000.0,
            currency="INR"
        )
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs

@router.put("", response_model=JobPreferencesOut)
def update_preferences(
    prefs_in: JobPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    prefs = db.query(JobPreferences).filter(JobPreferences.user_id == current_user.id).first()
    if not prefs:
        prefs = JobPreferences(user_id=current_user.id)
        db.add(prefs)
        
    update_data = prefs_in.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(prefs, key, val)
        
    db.commit()
    db.refresh(prefs)
    return prefs
