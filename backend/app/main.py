import os
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import Base, engine, SessionLocal, sync_database_schema
from app.routers import (
    auth, profile, resumes, preferences, jobs, matches, applications, dashboard, notifications
)
from app.routers.jobs import run_job_ingestion

# Create database tables and sync columns
sync_database_schema()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Personalized Job Discovery, AI Matching & Human-In-The-Loop Career Agent SaaS Platform",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(profile.router, prefix=settings.API_V1_STR)
app.include_router(resumes.router, prefix=settings.API_V1_STR)
app.include_router(preferences.router, prefix=settings.API_V1_STR)
app.include_router(jobs.router, prefix=settings.API_V1_STR)
app.include_router(matches.router, prefix=settings.API_V1_STR)
app.include_router(applications.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router, prefix=settings.API_V1_STR)
app.include_router(notifications.router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    """Initializes demo user and seed job database if empty."""
    db = SessionLocal()
    try:
        from app.models import Job, User
        # Seed default user if not exists
        user = db.query(User).filter(User.email == "vishal.aiml@example.com").first()
        if not user:
            from app.services.auth_service import get_password_hash
            from app.models import CandidateProfile, JobPreferences
            user = User(
                email="vishal.aiml@example.com",
                hashed_password=get_password_hash("password123"),
                full_name="Vishal Sharma"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            profile = CandidateProfile(
                user_id=user.id,
                full_name="Vishal Sharma",
                email="vishal.aiml@example.com",
                phone="+91 9876543210",
                phone_number="+91 9876543210",
                college_name="IIT Delhi",
                degree="B.Tech in Computer Science & Engineering",
                cgpa="8.8/10",
                graduation_year=2025,
                schooling={
                    "class_10th": {"school": "Delhi Public School", "board": "CBSE", "percentage": "95%"},
                    "class_12th": {"school": "Delhi Public School", "board": "CBSE", "percentage": "94%"}
                },
                location="Bangalore, India",
                headline="AI / Computer Vision Engineer | PyTorch, Deep Learning",
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
                    "organization": "AI Vision Labs",
                    "role": "Computer Vision & ML Intern",
                    "duration": "6 months",
                    "responsibilities": [
                        "Implemented YOLOv8 and PyTorch visual recognition models.",
                        "Deployed containerized inference services with Docker."
                    ]
                }],
                projects=[{
                    "title": "Real-Time Object Detection & Tracking",
                    "description": "Engineered custom PyTorch deep learning pipeline for high-speed object detection in video streams.",
                    "technologies": ["Python", "PyTorch", "OpenCV", "Docker"],
                    "achievements": "Achieved 92% mAP at 45 FPS."
                }],
                certifications=[
                    {"name": "Deep Learning Specialization", "organization": "DeepLearning.AI", "date": "2024"}
                ],
                summary="Passionate AI & Machine Learning engineer specialized in Computer Vision and Deep Learning with PyTorch and Python."
            )
            prefs = JobPreferences(
                user_id=user.id,
                preferred_roles=["AI Engineer", "Machine Learning Engineer", "Computer Vision Engineer"],
                employment_types=["Internship", "Full-time"],
                experience_levels=["Fresher", "0-1 years"],
                locations=["Bangalore", "Hyderabad", "Remote", "Pune"],
                remote_only=False,
                min_stipend=25000.0,
                min_salary=600000.0,
                currency="INR"
            )
            db.add(profile)
            db.add(prefs)
            db.commit()
        else:
            # Backfill existing user profile if fields are empty
            if user.profile:
                if not user.profile.college_name:
                    user.profile.college_name = "IIT Delhi"
                if not user.profile.cgpa:
                    user.profile.cgpa = "8.8/10"
                if not user.profile.degree:
                    user.profile.degree = "B.Tech in Computer Science & Engineering"
                if not user.profile.graduation_year:
                    user.profile.graduation_year = 2025
                if not user.profile.phone_number:
                    user.profile.phone_number = "+91 9876543210"
                    user.profile.phone = "+91 9876543210"
                if not user.profile.schooling:
                    user.profile.schooling = {
                        "class_10th": {"school": "Delhi Public School", "board": "CBSE", "percentage": "95%"},
                        "class_12th": {"school": "Delhi Public School", "board": "CBSE", "percentage": "94%"}
                    }
                db.commit()
            
        # Check if jobs exist
        job_count = db.query(Job).count()
        if job_count == 0:
            print("Seeding initial job opportunities instantly...")
            from app.services.job_sources.seed_feed import SeedFeedSource
            from app.services.deduplicator import generate_dedup_fingerprint
            from app.models import JobSource, Company, JobRequirement
            
            feed = SeedFeedSource()
            source_rec = JobSource(name=feed.name, source_type=feed.source_type)
            db.add(source_rec)
            db.commit()
            db.refresh(source_rec)
            
            seed_jobs = await feed.fetch_jobs()
            for nj in seed_jobs:
                fp = generate_dedup_fingerprint(nj.company_name, nj.title, nj.location)
                if db.query(Job).filter(Job.dedup_fingerprint == fp).first():
                    continue
                comp = db.query(Company).filter(Company.name == nj.company_name).first()
                if not comp:
                    comp = Company(name=nj.company_name)
                    db.add(comp)
                    db.commit()
                    db.refresh(comp)
                j = Job(
                    source_id=source_rec.id,
                    company_id=comp.id,
                    external_id=nj.external_id,
                    company_name=nj.company_name,
                    title=nj.title,
                    description=nj.description,
                    location=nj.location,
                    remote_type=nj.remote_type,
                    salary_min=nj.salary_min,
                    salary_max=nj.salary_max,
                    stipend=nj.stipend,
                    currency=nj.currency,
                    employment_type=nj.employment_type,
                    experience_level=nj.experience_level,
                    min_experience_years=nj.min_experience_years,
                    application_url=nj.application_url,
                    posted_at=nj.posted_at,
                    deadline=nj.deadline,
                    dedup_fingerprint=fp,
                    is_active=True
                )
                db.add(j)
                db.commit()
                db.refresh(j)
                req = JobRequirement(
                    job_id=j.id,
                    role_category=nj.role_category,
                    required_skills=nj.required_skills,
                    preferred_skills=nj.preferred_skills,
                    nice_to_have_skills=nj.nice_to_have_skills,
                    responsibilities=nj.responsibilities,
                    education_requirement=nj.education_requirement,
                    experience_years_required=nj.min_experience_years
                )
                db.add(req)
                db.commit()
    finally:
        db.close()

@app.get("/")
def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "status": "healthy",
        "docs": "/docs"
    }
