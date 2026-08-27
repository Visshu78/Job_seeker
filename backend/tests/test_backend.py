import pytest
import asyncio
from app.services.deduplicator import generate_dedup_fingerprint, is_duplicate
from app.services.matching_engine import hard_filter, compute_skill_matching, evaluate_job_match
from app.services.gap_analyzer import generate_gap_analysis
from app.services.application_agent import generate_cover_letter, generate_screening_answers
from app.services.resume_parser import parse_resume_text
from app.services.job_sources.linkedin_source import LinkedInSource
from app.services.auth_service import get_password_hash, verify_password, create_access_token, decode_token
from app.database import SessionLocal, engine, Base, sync_database_schema
from app.models import User, CandidateProfile
from app.routers.auth import google_auth
from app.schemas import GoogleAuthRequest

# Ensure columns and schema are synced
sync_database_schema()

def test_resume_parser():
    sample_text = """
    Vishal Sharma
    Email: vishal.aiml@example.com | Phone: +91 9876543210
    Bangalore, Karnataka
    
    Education:
    B.Tech in Computer Science, 2025, GPA: 8.8/10
    
    Skills:
    Python, PyTorch, OpenCV, Deep Learning, Docker, SQL, Git
    
    Projects:
    Object Detection System: Built real-time YOLO vision pipeline in PyTorch and OpenCV.
    """
    parsed = parse_resume_text(sample_text)
    assert parsed["full_name"] == "Vishal Sharma"
    assert "Python" in parsed["skills"]
    assert "PyTorch" in parsed["skills"]
    assert "OpenCV" in parsed["skills"]
    assert len(parsed["projects"]) > 0

def test_deduplication():
    fp1 = generate_dedup_fingerprint("XYZ Labs", "ML Engineer Intern", "Bangalore")
    fp2 = generate_dedup_fingerprint("XYZ Labs AI", "Machine Learning Intern", "Bengaluru")
    assert fp1 == fp2  # Matches canonical fingerprint

    is_dup = is_duplicate(
        "ML Engineer Intern", "XYZ Labs", "Seeking ML intern with PyTorch and Python in Bangalore",
        "Machine Learning Engineering Intern", "XYZ Labs AI", "Hiring Machine Learning Intern with PyTorch and Python in Bangalore"
    )
    assert is_dup is True

def test_matching_and_gap_analysis():
    candidate_profile = {
        "full_name": "Vishal Sharma",
        "skills": ["Python", "PyTorch", "OpenCV", "Deep Learning", "Docker"],
        "roles": ["Machine Learning Engineer", "Computer Vision Engineer"],
        "years_of_experience": 0.5,
        "education": [{"degree": "B.Tech"}],
        "projects": [{"title": "Vision System", "description": "PyTorch model"}]
    }
    
    job = {
        "id": 1,
        "company_name": "XYZ Labs",
        "title": "ML Engineer Intern",
        "description": "Looking for ML Intern in Bangalore with Python, PyTorch, AWS, and TensorFlow.",
        "location": "Bengaluru, Karnataka",
        "remote_type": "hybrid",
        "stipend": 35000.0,
        "employment_type": "Internship",
        "min_experience_years": 0.0,
        "requirements": {
            "required_skills": ["Python", "PyTorch", "TensorFlow"],
            "preferred_skills": ["AWS", "Docker"],
            "nice_to_have_skills": ["Kubernetes"]
        }
    }
    
    preferences = {
        "preferred_roles": ["Machine Learning Engineer", "AI Engineer"],
        "employment_types": ["Internship"],
        "locations": ["Bangalore"],
        "min_stipend": 25000.0,
        "remote_only": False,
        "excluded_companies": []
    }
    
    passed, reason = hard_filter(job, preferences)
    assert passed is True
    
    match_result = evaluate_job_match(candidate_profile, job, preferences)
    assert match_result["overall_score"] >= 75.0
    
    trans_reqs = [t["required"] for t in match_result["transferable_skills"]]
    assert "TensorFlow" in trans_reqs
    
    gap_result = generate_gap_analysis(match_result, candidate_profile, job)
    assert len(gap_result["resume_suggestions"]) > 0

def test_linkedin_source():
    source = LinkedInSource()
    jobs = asyncio.run(source.fetch_jobs())
    assert len(jobs) > 0
    assert any(j.source_name == "LinkedIn" for j in jobs)

def test_password_hashing_and_jwt():
    plain = "SecurePassword@123"
    hashed = get_password_hash(plain)
    assert hashed != plain
    assert len(hashed) > 20
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

    token = create_access_token(101)
    user_id = decode_token(token)
    assert user_id == "101"

def test_google_oauth_and_academic_fields():
    db = SessionLocal()
    try:
        # Test Google OAuth signup & profile seed
        auth_req = GoogleAuthRequest(
            email="test.student@google.com",
            full_name="Aarav Patel",
            google_id="g_1029384756",
            college_name="IIT Bombay",
            cgpa="9.1/10",
            phone_number="+91 9988776655"
        )
        res = google_auth(auth_req, db)
        assert res.access_token is not None
        assert res.user.email == "test.student@google.com"

        user = db.query(User).filter(User.email == "test.student@google.com").first()
        assert user is not None
        assert user.auth_provider == "google"
        assert user.google_id == "g_1029384756"
        assert user.hashed_password is not None

        # Check candidate profile academic & schooling details
        profile = user.profile
        assert profile is not None
        assert profile.college_name == "IIT Bombay"
        assert profile.cgpa == "9.1/10"
        assert profile.phone_number == "+91 9988776655"
        assert "class_10th" in profile.schooling
        assert "class_12th" in profile.schooling
        assert "Python" in profile.skills
    finally:
        db.close()

def test_otp_and_password_reset():
    db = SessionLocal()
    try:
        from app.routers.auth import send_otp, verify_otp, forgot_password, reset_password
        from app.schemas import SendOTPRequest, VerifyOTPRequest, ForgotPasswordRequest, ResetPasswordRequest

        email = "otp.test@example.com"
        
        # 1. Send OTP
        send_req = SendOTPRequest(email=email, purpose="email_verification")
        send_res = send_otp(send_req, db)
        assert send_res["otp_code"] is not None
        otp_code = send_res["otp_code"]

        # 2. Verify OTP
        verify_req = VerifyOTPRequest(email=email, otp_code=otp_code, purpose="email_verification")
        verify_res = verify_otp(verify_req, db)
        assert verify_res["email"] == email

        # 3. Forgot password OTP flow
        user = db.query(User).filter(User.email == "test.student@google.com").first()
        if user:
            fp_req = ForgotPasswordRequest(email=user.email)
            fp_res = forgot_password(fp_req, db)
            reset_code = fp_res["otp_code"]

            # Reset password
            reset_req = ResetPasswordRequest(email=user.email, otp_code=reset_code, new_password="NewSecurePassword@123")
            reset_res = reset_password(reset_req, db)
            assert "successful" in reset_res["message"]

            # Verify password update
            updated_user = db.query(User).filter(User.email == user.email).first()
            assert verify_password("NewSecurePassword@123", updated_user.hashed_password) is True
    finally:
        db.close()
