from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Job, CandidateProfile, JobPreferences, JobMatch, Resume, Notification
from app.schemas import JobMatchOut
from app.routers.deps import get_current_user
from app.services.matching_engine import hard_filter, evaluate_job_match
from app.services.gap_analyzer import generate_gap_analysis

router = APIRouter(prefix="/matches", tags=["Matches & Gap Analysis"])

def sync_user_matches(user_id: int, db: Session):
    """Evaluates all active jobs against the user's profile and preferences."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    prefs = db.query(JobPreferences).filter(JobPreferences.user_id == user_id).first()
    
    if not profile or not prefs:
        return
        
    profile_dict = {
        "full_name": profile.full_name,
        "roles": profile.roles or [],
        "skills": profile.skills or [],
        "years_of_experience": profile.years_of_experience or 0.0,
        "education": profile.education or [],
        "experience": profile.experience or [],
        "projects": profile.projects or [],
        "summary": profile.summary or ""
    }
    
    prefs_dict = {
        "preferred_roles": prefs.preferred_roles or [],
        "employment_types": prefs.employment_types or [],
        "locations": prefs.locations or [],
        "remote_only": prefs.remote_only or False,
        "min_salary": prefs.min_salary or 0.0,
        "min_stipend": prefs.min_stipend or 0.0,
        "excluded_companies": prefs.excluded_companies or []
    }
    
    resume_text = ""
    primary_resume = db.query(Resume).filter(Resume.user_id == user_id, Resume.is_primary == True).first()
    if primary_resume and primary_resume.raw_text:
        resume_text = primary_resume.raw_text
        
    active_jobs = db.query(Job).filter(Job.is_active == True).all()
    
    for job in active_jobs:
        job_dict = {
            "id": job.id,
            "company_name": job.company_name,
            "title": job.title,
            "description": job.description,
            "location": job.location,
            "remote_type": job.remote_type,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "stipend": job.stipend,
            "employment_type": job.employment_type,
            "min_experience_years": job.min_experience_years,
            "requirements": {
                "required_skills": job.requirements.required_skills if job.requirements else [],
                "preferred_skills": job.requirements.preferred_skills if job.requirements else [],
                "nice_to_have_skills": job.requirements.nice_to_have_skills if job.requirements else []
            }
        }
        
        # Step 1: Hard Filtering (PRD Section 19)
        passed_filter, reason = hard_filter(job_dict, prefs_dict)
        if not passed_filter:
            # If match previously existed, we can mark or skip
            continue
            
        # Step 2: Multi-Factor AI Matching (PRD Section 20 & 21)
        match_result = evaluate_job_match(profile_dict, job_dict, prefs_dict, resume_text)
        
        # Step 3: Gap Analysis & Resume Suggestions (PRD Section 23, 24, 25)
        gap_result = generate_gap_analysis(match_result, profile_dict, job_dict)
        
        # Check if match already saved
        existing_match = db.query(JobMatch).filter(
            JobMatch.user_id == user_id,
            JobMatch.job_id == job.id
        ).first()
        
        if existing_match:
            # Preserve user's save / skip decisions
            existing_match.overall_score = match_result["overall_score"]
            existing_match.skill_score = match_result["skill_score"]
            existing_match.semantic_score = match_result["semantic_score"]
            existing_match.experience_score = match_result["experience_score"]
            existing_match.preference_score = match_result["preference_score"]
            existing_match.role_score = match_result["role_score"]
            existing_match.education_score = match_result["education_score"]
            existing_match.recommendation_tier = match_result["recommendation_tier"]
            existing_match.matched_skills = match_result["matched_skills"]
            existing_match.missing_skills = match_result["missing_skills"]
            existing_match.transferable_skills = match_result["transferable_skills"]
            existing_match.partial_skills = match_result["partial_skills"]
            existing_match.why_recommended = gap_result["why_recommended"]
            existing_match.gap_summary = gap_result["gap_summary"]
            existing_match.resume_suggestions = gap_result["resume_suggestions"]
            existing_match.updated_at = datetime.utcnow()
        else:
            new_match = JobMatch(
                user_id=user_id,
                job_id=job.id,
                overall_score=match_result["overall_score"],
                skill_score=match_result["skill_score"],
                semantic_score=match_result["semantic_score"],
                experience_score=match_result["experience_score"],
                preference_score=match_result["preference_score"],
                role_score=match_result["role_score"],
                education_score=match_result["education_score"],
                recommendation_tier=match_result["recommendation_tier"],
                matched_skills=match_result["matched_skills"],
                missing_skills=match_result["missing_skills"],
                transferable_skills=match_result["transferable_skills"],
                partial_skills=match_result["partial_skills"],
                why_recommended=gap_result["why_recommended"],
                gap_summary=gap_result["gap_summary"],
                resume_suggestions=gap_result["resume_suggestions"],
                is_saved=False,
                is_skipped=False,
                is_notified=False
            )
            db.add(new_match)
            db.flush()
            
            # Trigger High-Match Notification if >= 85%
            if match_result["overall_score"] >= 85.0:
                notif = Notification(
                    user_id=user_id,
                    job_id=job.id,
                    match_id=new_match.id,
                    title=f"{int(match_result['overall_score'])}% Match — {job.title}",
                    message=f"High Priority Opportunity at {job.company_name} in {job.location}. Strong skill match in {', '.join([m['skill'] for m in match_result['matched_skills'][:3]])}.",
                    notification_type="high_match",
                    score=match_result["overall_score"]
                )
                db.add(notif)
                new_match.is_notified = True

    db.commit()

@router.get("", response_model=List[JobMatchOut])
def get_matches(
    tier: Optional[str] = None,
    saved_only: bool = False,
    include_skipped: bool = False,
    min_score: float = 0.0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Ensure matches are calculated
    sync_user_matches(current_user.id, db)
    
    query = db.query(JobMatch).filter(JobMatch.user_id == current_user.id)
    
    if not include_skipped:
        query = query.filter(JobMatch.is_skipped == False)
    if saved_only:
        query = query.filter(JobMatch.is_saved == True)
    if tier:
        query = query.filter(JobMatch.recommendation_tier == tier)
    if min_score > 0:
        query = query.filter(JobMatch.overall_score >= min_score)
        
    matches = query.order_by(JobMatch.overall_score.desc()).all()
    return matches

@router.get("/{match_id}", response_model=JobMatchOut)
def get_match_detail(match_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    match = db.query(JobMatch).filter(JobMatch.id == match_id, JobMatch.user_id == current_user.id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match

@router.post("/{match_id}/save")
def save_match(match_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    match = db.query(JobMatch).filter(JobMatch.id == match_id, JobMatch.user_id == current_user.id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    match.is_saved = True
    match.is_skipped = False
    db.commit()
    return {"message": "Opportunity saved successfully", "is_saved": True}

@router.post("/{match_id}/skip")
def skip_match(match_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    match = db.query(JobMatch).filter(JobMatch.id == match_id, JobMatch.user_id == current_user.id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    match.is_skipped = True
    match.is_saved = False
    db.commit()
    return {"message": "Opportunity skipped", "is_skipped": True}

@router.post("/recalculate")
def recalculate_matches(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sync_user_matches(current_user.id, db)
    return {"message": "Matches successfully re-evaluated against latest profile & preferences"}
