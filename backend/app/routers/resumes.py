import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Resume, CandidateProfile
from app.schemas import ResumeOut, CandidateProfileOut
from app.routers.deps import get_current_user
from app.config import settings
from app.services.resume_parser import extract_text_from_file, parse_resume_text

router = APIRouter(prefix="/resumes", tags=["Resumes"])

@router.get("", response_model=List[ResumeOut])
def get_resumes(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resumes = db.query(Resume).filter(Resume.user_id == current_user.id).order_by(Resume.created_at.desc()).all()
    return resumes

@router.post("/upload", response_model=CandidateProfileOut)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".docx", ".txt"]:
        raise HTTPException(status_code=400, detail="Only PDF, DOCX, and TXT formats are supported.")
    
    file_path = os.path.join(settings.UPLOAD_DIR, f"user_{current_user.id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    raw_text = extract_text_from_file(file_path, ext)
    
    # Save Resume Record
    resume = Resume(
        user_id=current_user.id,
        filename=file.filename,
        file_path=file_path,
        file_type=ext.replace(".", ""),
        raw_text=raw_text,
        is_primary=True
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    
    # Parse resume into structured profile
    parsed = parse_resume_text(raw_text)
    
    # Update or create candidate profile
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        profile = CandidateProfile(user_id=current_user.id)
        db.add(profile)
        
    profile.resume_id = resume.id
    profile.full_name = parsed["full_name"] or current_user.full_name
    profile.email = parsed["email"] or current_user.email
    profile.phone = parsed["phone"]
    profile.location = parsed["location"]
    profile.headline = parsed["headline"]
    profile.roles = parsed["roles"]
    profile.experience_level = parsed["experience_level"]
    profile.years_of_experience = parsed["years_of_experience"]
    profile.skills = parsed["skills"]
    profile.education = parsed["education"]
    profile.experience = parsed["experience"]
    profile.projects = parsed["projects"]
    profile.certifications = parsed["certifications"]
    profile.summary = parsed["summary"]
    
    db.commit()
    db.refresh(profile)
    
    return profile

@router.delete("/{resume_id}")
def delete_resume(resume_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    if os.path.exists(resume.file_path):
        try:
            os.remove(resume.file_path)
        except Exception:
            pass
            
    db.delete(resume)
    db.commit()
    return {"message": "Resume deleted successfully"}
