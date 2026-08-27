from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

# ----------------- User & Auth Schemas -----------------
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    auth_provider: Optional[str] = "local"

class UserCreate(UserBase):
    password: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class GoogleAuthRequest(BaseModel):
    id_token: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    google_id: Optional[str] = None
    college_name: Optional[str] = None
    cgpa: Optional[str] = None
    phone_number: Optional[str] = None

class SendOTPRequest(BaseModel):
    email: EmailStr
    purpose: str = "email_verification"

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp_code: str
    purpose: str = "email_verification"

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp_code: str
    new_password: str

class UserOut(UserBase):
    id: int
    is_active: bool
    is_verified: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut

class TokenPayload(BaseModel):
    sub: Optional[str] = None


# ----------------- Candidate Profile Schemas -----------------
class SchoolingItem(BaseModel):
    class_10th: Optional[Dict[str, Any]] = None  # {"school": "DPS", "board": "CBSE", "percentage": "95%"}
    class_12th: Optional[Dict[str, Any]] = None  # {"school": "DPS", "board": "CBSE", "percentage": "94%"}

class EducationItem(BaseModel):
    degree: str
    field: Optional[str] = None
    institution: Optional[str] = None
    graduation_year: Optional[int] = None
    gpa: Optional[str] = None

class ExperienceItem(BaseModel):
    organization: str
    role: str
    duration: Optional[str] = None
    responsibilities: List[str] = []

class ProjectItem(BaseModel):
    title: str
    description: str
    technologies: List[str] = []
    achievements: Optional[str] = None

class CertificationItem(BaseModel):
    name: str
    organization: Optional[str] = None
    date: Optional[str] = None

class CandidateProfileBase(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None
    headline: Optional[str] = None
    
    # Academic & Student fields
    college_name: Optional[str] = None
    degree: Optional[str] = None
    cgpa: Optional[str] = None
    graduation_year: Optional[int] = None
    schooling: Optional[Dict[str, Any]] = {}
    
    roles: List[str] = []
    experience_level: Optional[str] = "entry_level"
    years_of_experience: float = 0.0
    skills: List[str] = []
    education: List[EducationItem] = []
    experience: List[ExperienceItem] = []
    projects: List[ProjectItem] = []
    certifications: List[CertificationItem] = []
    summary: Optional[str] = None

class CandidateProfileUpdate(CandidateProfileBase):
    pass

class CandidateProfileOut(CandidateProfileBase):
    id: int
    user_id: int
    resume_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ----------------- Resume Schemas -----------------
class ResumeOut(BaseModel):
    id: int
    filename: str
    file_type: str
    is_primary: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ----------------- Job Preference Schemas -----------------
class JobPreferencesBase(BaseModel):
    preferred_roles: List[str] = ["AI Engineer", "Machine Learning Engineer", "Software Engineer"]
    employment_types: List[str] = ["Internship", "Full-time"]
    experience_levels: List[str] = ["Fresher", "0-1 years", "1-2 years"]
    locations: List[str] = ["Bangalore", "Hyderabad", "Remote", "Pune", "Delhi NCR"]
    remote_only: bool = False
    min_salary: float = 0.0
    min_stipend: float = 20000.0
    currency: str = "INR"
    preferred_companies: List[str] = []
    excluded_companies: List[str] = []
    target_skills: List[str] = []

class JobPreferencesUpdate(JobPreferencesBase):
    pass

class JobPreferencesOut(JobPreferencesBase):
    id: int
    user_id: int
    updated_at: datetime

    class Config:
        from_attributes = True


# ----------------- Job Schemas -----------------
class JobRequirementOut(BaseModel):
    role_category: Optional[str] = None
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    nice_to_have_skills: List[str] = []
    responsibilities: List[str] = []
    education_requirement: Optional[str] = None
    experience_years_required: float = 0.0

    class Config:
        from_attributes = True

class JobOut(BaseModel):
    id: int
    source_name: Optional[str] = None
    company_name: str
    title: str
    description: str
    location: str
    remote_type: str
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    stipend: Optional[float] = None
    currency: str
    employment_type: str
    experience_level: str
    min_experience_years: float
    application_url: str
    posted_at: datetime
    is_active: bool
    requirements: Optional[JobRequirementOut] = None

    class Config:
        from_attributes = True


# ----------------- Job Matching & Gap Schemas -----------------
class SkillMatchDetail(BaseModel):
    skill: str
    type: str  # REQUIRED, PREFERRED, NICE_TO_HAVE

class MissingSkillDetail(BaseModel):
    skill: str
    type: str
    severity: str  # HIGH, MEDIUM, LOW

class TransferableSkillDetail(BaseModel):
    required: str
    candidate_has: str
    explanation: str

class ResumeSuggestion(BaseModel):
    category: str  # skill_highlight, project_enhancement, keyword_inclusion
    title: str
    suggestion: str
    reason: str
    evidence_in_resume: Optional[str] = None

class JobMatchOut(BaseModel):
    id: int
    job_id: int
    job: JobOut
    overall_score: float
    skill_score: float
    semantic_score: float
    experience_score: float
    preference_score: float
    role_score: float
    education_score: float
    recommendation_tier: str  # HIGH_PRIORITY, CONSIDER, LOW_PRIORITY
    matched_skills: List[Dict[str, Any]] = []
    missing_skills: List[Dict[str, Any]] = []
    transferable_skills: List[Dict[str, Any]] = []
    partial_skills: List[Dict[str, Any]] = []
    why_recommended: Optional[str] = None
    gap_summary: Optional[str] = None
    resume_suggestions: List[Dict[str, Any]] = []
    is_saved: bool
    is_skipped: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ----------------- Application Preparation & Review Schemas -----------------
class ApplicationPrepareRequest(BaseModel):
    job_id: int
    tailor_resume: bool = True
    generate_cover_letter: bool = True

class ApplicationPrepareResponse(BaseModel):
    job_id: int
    job_title: str
    company_name: str
    candidate_name: str
    recommended_resume_id: Optional[int] = None
    cover_letter: str
    screening_answers: Dict[str, str]
    tailoring_suggestions: List[str]

class ApplicationConfirmRequest(BaseModel):
    user_reviewed: bool = Field(..., description="Must be true to confirm application")
    user_authorized: bool = Field(..., description="Must be true to confirm submission authorization")
    cover_letter: Optional[str] = None
    screening_answers: Optional[Dict[str, str]] = None
    notes: Optional[str] = None

class ApplicationOut(BaseModel):
    id: int
    job_id: int
    job: JobOut
    status: str
    cover_letter: Optional[str] = None
    screening_answers: Dict[str, Any] = {}
    user_reviewed: bool
    user_authorized: bool
    approved_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ApplicationStatusUpdate(BaseModel):
    status: str  # DISCOVERED, SAVED, APPROVED, PREPARING, SUBMITTED, UNDER_REVIEW, INTERVIEW, OFFER, REJECTED
    notes: Optional[str] = None


# ----------------- Dashboard & Analytics Schemas -----------------
class DashboardStats(BaseModel):
    jobs_discovered_today: int
    total_active_jobs: int
    high_fit_matches_count: int
    recommended_count: int
    applications_total: int
    applications_submitted: int
    interviews_count: int
    offers_count: int
    average_match_score: float
    best_matching_role: str
    top_location: str
    top_skill_cluster: str

class NotificationOut(BaseModel):
    id: int
    job_id: Optional[int] = None
    match_id: Optional[int] = None
    title: str
    message: str
    notification_type: str
    score: Optional[float] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
