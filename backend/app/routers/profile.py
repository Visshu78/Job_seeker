from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, CandidateProfile
from app.schemas import CandidateProfileOut, CandidateProfileUpdate
from app.routers.deps import get_current_user

router = APIRouter(prefix="/profile", tags=["Candidate Profile"])

@router.get("", response_model=CandidateProfileOut)
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        profile = CandidateProfile(
            user_id=current_user.id,
            full_name=current_user.full_name or "Vishal Sharma",
            email=current_user.email,
            phone="+91 9876543210",
            phone_number="+91 9876543210",
            college_name="National Institute of Technology",
            degree="B.Tech in Computer Science & Engineering",
            cgpa="8.7/10",
            graduation_year=2025,
            schooling={
                "class_10th": {"school": "Delhi Public School", "board": "CBSE", "percentage": "95%"},
                "class_12th": {"school": "Delhi Public School", "board": "CBSE", "percentage": "94%"}
            },
            location="Bangalore, India",
            headline="AI/ML Engineer | PyTorch, Computer Vision, Deep Learning",
            roles=["Machine Learning Engineer", "Computer Vision Engineer", "AI Engineer"],
            experience_level="Fresher",
            years_of_experience=0.5,
            skills=["Python", "PyTorch", "OpenCV", "Deep Learning", "Docker", "Git", "SQL"],
            education=[{
                "degree": "B.Tech in Computer Science & Engineering",
                "field": "Artificial Intelligence",
                "institution": "National Institute of Technology",
                "graduation_year": 2025,
                "gpa": "8.7/10"
            }],
            experience=[{
                "organization": "AI Vision Research Lab",
                "role": "Computer Vision & ML Intern",
                "duration": "6 months",
                "responsibilities": [
                    "Implemented YOLOv8 and PyTorch visual recognition models.",
                    "Deployed containerized inference services with Docker."
                ]
            }],
            projects=[{
                "title": "Real-Time Multi-Object Detection & Tracking",
                "description": "Engineered custom PyTorch deep learning pipeline for high-speed object detection in video streams.",
                "technologies": ["Python", "PyTorch", "OpenCV", "Docker"],
                "achievements": "Achieved 92% mAP at 45 FPS."
            }],
            certifications=[
                {"name": "Deep Learning Specialization", "organization": "DeepLearning.AI", "date": "2024"}
            ],
            summary="Passionate AI & Machine Learning engineer specialized in Computer Vision and Deep Learning with PyTorch and Python."
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

@router.put("", response_model=CandidateProfileOut)
def update_profile(
    profile_in: CandidateProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        profile = CandidateProfile(user_id=current_user.id)
        db.add(profile)
        
    update_data = profile_in.model_dump(exclude_unset=True)
    # Convert Pydantic submodels to dicts for JSON columns
    for key, val in update_data.items():
        if isinstance(val, list):
            serialized_list = []
            for item in val:
                if hasattr(item, "model_dump"):
                    serialized_list.append(item.model_dump())
                else:
                    serialized_list.append(item)
            setattr(profile, key, serialized_list)
        else:
            setattr(profile, key, val)
            
    db.commit()
    db.refresh(profile)
    return profile
