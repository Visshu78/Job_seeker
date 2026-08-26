from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # Nullable for OAuth users
    full_name = Column(String(255), nullable=True)
    phone_number = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    auth_provider = Column(String(50), default="local")  # "local", "google"
    google_id = Column(String(255), unique=True, index=True, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    profile = relationship("CandidateProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    preferences = relationship("JobPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    matches = relationship("JobMatch", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, txt
    raw_text = Column(Text, nullable=True)
    is_primary = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="resumes")
    profiles = relationship("CandidateProfile", back_populates="resume")


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)
    
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(100), nullable=True)
    phone_number = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)
    headline = Column(String(255), nullable=True)
    
    # Academic & Student credentials
    college_name = Column(String(255), nullable=True)  # e.g., "IIT Delhi", "BITS Pilani", "RVCE"
    degree = Column(String(100), nullable=True)  # e.g., "B.Tech in Computer Science"
    cgpa = Column(String(50), nullable=True)  # e.g., "8.8/10", "9.2"
    graduation_year = Column(Integer, nullable=True)  # e.g., 2025
    schooling = Column(JSON, default=dict)  # {"class_10th": {"school": "DPS", "board": "CBSE", "percentage": "95%"}, "class_12th": {"school": "DPS", "board": "CBSE", "percentage": "94%"}}
    
    # Structured technical representations
    roles = Column(JSON, default=list)  # ["Machine Learning Engineer", "Software Engineer"]
    experience_level = Column(String(50), default="entry_level")  # fresher, 0-1, 1-2, 2-3, mid, senior
    years_of_experience = Column(Float, default=0.0)
    skills = Column(JSON, default=list)  # ["Python", "PyTorch", "OpenCV", "Docker"]
    education = Column(JSON, default=list)  # [{"degree": "B.Tech", "field": "Computer Science", "institution": "IIT", "graduation_year": 2025, "gpa": "8.5"}]
    experience = Column(JSON, default=list)  # [{"organization": "XYZ", "role": "ML Intern", "duration": "6 months", "responsibilities": ["..."]}]
    projects = Column(JSON, default=list)  # [{"title": "Object Detection", "description": "...", "technologies": ["PyTorch", "OpenCV"]}]
    certifications = Column(JSON, default=list)  # [{"name": "AWS Certified", "organization": "Amazon", "date": "2024"}]
    summary = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")
    resume = relationship("Resume", back_populates="profiles")


class JobPreferences(Base):
    __tablename__ = "job_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    preferred_roles = Column(JSON, default=lambda: ["AI Engineer", "Machine Learning Engineer", "Software Engineer"])
    employment_types = Column(JSON, default=lambda: ["Internship", "Full-time"])  # Internship, Full-time, Contract, Part-time
    experience_levels = Column(JSON, default=lambda: ["Fresher", "0-1 years", "1-2 years"])
    locations = Column(JSON, default=lambda: ["Bangalore", "Hyderabad", "Remote", "Pune", "Delhi NCR"])
    remote_only = Column(Boolean, default=False)
    
    min_salary = Column(Float, default=0.0)  # e.g., 600000 INR/year
    min_stipend = Column(Float, default=20000.0)  # e.g., 20000 INR/month
    currency = Column(String(10), default="INR")
    
    preferred_companies = Column(JSON, default=list)
    excluded_companies = Column(JSON, default=list)
    target_skills = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="preferences")


class JobSource(Base):
    __tablename__ = "job_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # Greenhouse, Lever, RemoteOK, Adzuna, Seed
    source_type = Column(String(50), nullable=False)  # ats_api, job_board, aggregator, feed
    base_url = Column(String(500), nullable=True)
    enabled = Column(Boolean, default=True)
    rate_limit = Column(Integer, default=60)
    last_success = Column(DateTime, nullable=True)
    last_failure = Column(DateTime, nullable=True)
    jobs_count = Column(Integer, default=0)

    jobs = relationship("Job", back_populates="source")


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    website = Column(String(500), nullable=True)
    logo_url = Column(String(500), nullable=True)
    domain = Column(String(255), nullable=True)

    jobs = relationship("Job", back_populates="company_rel")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("job_sources.id"), nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    
    external_id = Column(String(255), nullable=True, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    location = Column(String(255), default="Remote", index=True)
    remote_type = Column(String(50), default="on-site")  # remote, hybrid, on-site
    
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    stipend = Column(Float, nullable=True)
    currency = Column(String(10), default="INR")
    
    employment_type = Column(String(50), default="Full-time")  # Internship, Full-time, Contract, Part-time
    experience_level = Column(String(50), default="Entry-level")  # Fresher, 0-1 years, 1-2 years, Mid-level, Senior
    min_experience_years = Column(Float, default=0.0)
    
    application_url = Column(String(1000), nullable=False)
    posted_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    deadline = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Deduplication fingerprint: hash of normalized company + title + location
    dedup_fingerprint = Column(String(255), index=True, nullable=True)
    duplicate_of_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)

    source = relationship("JobSource", back_populates="jobs")
    company_rel = relationship("Company", back_populates="jobs")
    requirements = relationship("JobRequirement", back_populates="job", uselist=False, cascade="all, delete-orphan")
    matches = relationship("JobMatch", back_populates="job", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="job")


class JobRequirement(Base):
    __tablename__ = "job_requirements"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, unique=True, index=True)
    
    role_category = Column(String(100), nullable=True)
    required_skills = Column(JSON, default=list)  # ["Python", "PyTorch", "Deep Learning"]
    preferred_skills = Column(JSON, default=list)  # ["Docker", "AWS"]
    nice_to_have_skills = Column(JSON, default=list)  # ["Kubernetes", "MLflow"]
    responsibilities = Column(JSON, default=list)
    education_requirement = Column(String(255), nullable=True)  # B.Tech / M.Tech in CS/AI or equivalent
    experience_years_required = Column(Float, default=0.0)

    job = relationship("Job", back_populates="requirements")


class JobMatch(Base):
    __tablename__ = "job_matches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    
    # Overall and Component Scores (0 to 100)
    overall_score = Column(Float, default=0.0, index=True)
    skill_score = Column(Float, default=0.0)
    semantic_score = Column(Float, default=0.0)
    experience_score = Column(Float, default=0.0)
    preference_score = Column(Float, default=0.0)
    role_score = Column(Float, default=0.0)
    education_score = Column(Float, default=0.0)
    
    # Recommendation tier: HIGH_PRIORITY, CONSIDER, LOW_PRIORITY
    recommendation_tier = Column(String(50), default="CONSIDER", index=True)
    
    # Detailed Gap & Match breakdown
    matched_skills = Column(JSON, default=list)  # [{"skill": "Python", "type": "REQUIRED"}, ...]
    missing_skills = Column(JSON, default=list)  # [{"skill": "AWS", "type": "PREFERRED", "severity": "MEDIUM"}, ...]
    transferable_skills = Column(JSON, default=list)  # [{"required": "TensorFlow", "candidate_has": "PyTorch", "explanation": "Strong PyTorch experience transfers"}]
    partial_skills = Column(JSON, default=list)
    
    why_recommended = Column(Text, nullable=True)
    gap_summary = Column(Text, nullable=True)
    resume_suggestions = Column(JSON, default=list)  # Suggestions to tailor resume without fabricating
    
    is_saved = Column(Boolean, default=False)
    is_skipped = Column(Boolean, default=False)
    is_notified = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="matches")
    job = relationship("Job", back_populates="matches")
    application = relationship("Application", back_populates="match", uselist=False)


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    match_id = Column(Integer, ForeignKey("job_matches.id"), nullable=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)
    
    # Statuses: DISCOVERED, SAVED, APPROVED, PREPARING, SUBMITTED, UNDER_REVIEW, INTERVIEW, OFFER, REJECTED
    status = Column(String(50), default="SAVED", index=True)
    
    # Application Artifacts
    tailored_resume_notes = Column(Text, nullable=True)
    cover_letter = Column(Text, nullable=True)
    screening_answers = Column(JSON, default=dict)  # {"Why XYZ Labs?": "...", "Notice period": "Immediate"}
    
    # Human-In-The-Loop Safety Gate Checkboxes
    user_reviewed = Column(Boolean, default=False)
    user_authorized = Column(Boolean, default=False)
    
    # Timestamps & Audit
    approved_at = Column(DateTime, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    applied_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    match = relationship("JobMatch", back_populates="application")
    events = relationship("ApplicationEvent", back_populates="application", cascade="all, delete-orphan")


class ApplicationEvent(Base):
    __tablename__ = "application_events"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)  # PREPARED, APPROVED, SUBMITTED, STATUS_CHANGED, NOTE_ADDED
    description = Column(Text, nullable=False)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="events")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    match_id = Column(Integer, ForeignKey("job_matches.id"), nullable=True)
    
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default="high_match")  # high_match, application_update, gap_alert
    score = Column(Float, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")
