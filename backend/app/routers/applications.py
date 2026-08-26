from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Job, JobMatch, Application, ApplicationEvent, CandidateProfile, Resume
from app.schemas import (
    ApplicationOut, ApplicationPrepareRequest, ApplicationPrepareResponse,
    ApplicationConfirmRequest, ApplicationStatusUpdate
)
from app.routers.deps import get_current_user
from app.services.application_agent import generate_cover_letter, generate_screening_answers

router = APIRouter(prefix="/applications", tags=["Applications & Tracking"])

@router.post("/prepare", response_model=ApplicationPrepareResponse)
def prepare_application(
    req: ApplicationPrepareRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == req.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Please complete candidate profile first")
        
    match = db.query(JobMatch).filter(JobMatch.user_id == current_user.id, JobMatch.job_id == job.id).first()
    matched_skills = match.matched_skills if match else []
    
    profile_dict = {
        "full_name": profile.full_name or current_user.full_name or "Candidate",
        "skills": profile.skills or [],
        "projects": profile.projects or [],
        "experience": profile.experience or [],
        "education": profile.education or []
    }
    job_dict = {
        "id": job.id,
        "company_name": job.company_name,
        "title": job.title,
        "description": job.description
    }
    
    cover_letter = generate_cover_letter(profile_dict, job_dict, matched_skills)
    screening_answers = generate_screening_answers(profile_dict, job_dict)
    
    tailoring_suggestions = []
    if match and match.resume_suggestions:
        tailoring_suggestions = [s.get("suggestion", "") for s in match.resume_suggestions]
    if not tailoring_suggestions:
        tailoring_suggestions = [
            f"Highlight your direct experience with {', '.join([m['skill'] for m in matched_skills[:3]])} in your project bullet points.",
            f"Emphasize impact metrics and latency/accuracy optimizations relevant to {job.company_name}."
        ]
        
    primary_resume = db.query(Resume).filter(Resume.user_id == current_user.id, Resume.is_primary == True).first()
    
    # Check or create Application in 'PREPARING' state
    app_record = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.job_id == job.id
    ).first()
    
    if not app_record:
        app_record = Application(
            user_id=current_user.id,
            job_id=job.id,
            match_id=match.id if match else None,
            resume_id=primary_resume.id if primary_resume else None,
            status="PREPARING",
            cover_letter=cover_letter,
            screening_answers=screening_answers
        )
        db.add(app_record)
        db.commit()
        db.refresh(app_record)
        
        # Log preparation event
        event = ApplicationEvent(
            application_id=app_record.id,
            event_type="PREPARED",
            description="Application materials (Cover Letter, Screening Q&A) prepared by AI Career Agent."
        )
        db.add(event)
        db.commit()

    return ApplicationPrepareResponse(
        job_id=job.id,
        job_title=job.title,
        company_name=job.company_name,
        candidate_name=profile_dict["full_name"],
        recommended_resume_id=primary_resume.id if primary_resume else None,
        cover_letter=cover_letter,
        screening_answers=screening_answers,
        tailoring_suggestions=tailoring_suggestions
    )


@router.post("/{app_id}/confirm", response_model=ApplicationOut)
def confirm_and_apply(
    app_id: int,
    confirm_req: ApplicationConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    PRD Section 30, 31, 55: Human-In-The-Loop Explicit Confirmation Gate.
    Strictly verifies user_reviewed and user_authorized are TRUE before submission.
    """
    if not confirm_req.user_reviewed or not confirm_req.user_authorized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Human confirmation safety gate violation: You must explicitly check both 'I reviewed this application' and 'I authorize submission' checkboxes."
        )
        
    app_record = db.query(Application).filter(
        Application.id == app_id,
        Application.user_id == current_user.id
    ).first()
    
    if not app_record:
        raise HTTPException(status_code=404, detail="Application record not found")
        
    app_record.user_reviewed = True
    app_record.user_authorized = True
    app_record.status = "SUBMITTED"
    app_record.approved_at = datetime.utcnow()
    app_record.submitted_at = datetime.utcnow()
    app_record.applied_at = datetime.utcnow()
    
    if confirm_req.cover_letter:
        app_record.cover_letter = confirm_req.cover_letter
    if confirm_req.screening_answers:
        app_record.screening_answers = confirm_req.screening_answers
    if confirm_req.notes:
        app_record.notes = confirm_req.notes
        
    # Audit trail event (PRD Section 55)
    event = ApplicationEvent(
        application_id=app_record.id,
        event_type="SUBMITTED",
        description=f"User explicitly reviewed and authorized submission for {app_record.job.title} at {app_record.job.company_name}.",
        metadata_json={
            "user_email": current_user.email,
            "timestamp": datetime.utcnow().isoformat(),
            "destination_url": app_record.job.application_url
        }
    )
    db.add(event)
    db.commit()
    db.refresh(app_record)
    
    return app_record


@router.get("", response_model=List[ApplicationOut])
def list_applications(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Application).filter(Application.user_id == current_user.id)
    if status:
        query = query.filter(Application.status == status)
    apps = query.order_by(Application.updated_at.desc()).all()
    return apps


@router.patch("/{app_id}/status", response_model=ApplicationOut)
def update_application_status(
    app_id: int,
    status_update: ApplicationStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app_record = db.query(Application).filter(
        Application.id == app_id,
        Application.user_id == current_user.id
    ).first()
    
    if not app_record:
        raise HTTPException(status_code=404, detail="Application record not found")
        
    old_status = app_record.status
    app_record.status = status_update.status
    if status_update.notes:
        app_record.notes = status_update.notes
        
    # Record event
    event = ApplicationEvent(
        application_id=app_record.id,
        event_type="STATUS_CHANGED",
        description=f"Application status updated from {old_status} to {status_update.status}."
    )
    db.add(event)
    db.commit()
    db.refresh(app_record)
    return app_record
