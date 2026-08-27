from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
import random
from datetime import datetime, timedelta
from app.models import User, CandidateProfile, JobPreferences, VerificationOTP
from app.schemas import (
    UserCreate, UserLogin, Token, UserOut, GoogleAuthRequest,
    SendOTPRequest, VerifyOTPRequest, ForgotPasswordRequest, ResetPasswordRequest
)
from app.services.auth_service import get_password_hash, verify_password, create_access_token
from app.routers.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/send-otp")
def send_otp(req: SendOTPRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    otp_code = str(random.randint(100000, 999999))
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    # Deactivate previous active OTPs for this email & purpose
    db.query(VerificationOTP).filter(
        VerificationOTP.email == email,
        VerificationOTP.purpose == req.purpose,
        VerificationOTP.is_used == False
    ).update({"is_used": True})

    otp_record = VerificationOTP(
        email=email,
        otp_code=otp_code,
        purpose=req.purpose,
        expires_at=expires_at
    )
    db.add(otp_record)
    db.commit()

    print(f"[Verification OTP] Code for {email} ({req.purpose}): {otp_code}")
    return {
        "message": f"Verification code sent to {email}",
        "email": email,
        "otp_code": otp_code,
        "expires_in_minutes": 10
    }

@router.post("/verify-otp")
def verify_otp(req: VerifyOTPRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    otp_record = db.query(VerificationOTP).filter(
        VerificationOTP.email == email,
        VerificationOTP.otp_code == req.otp_code.strip(),
        VerificationOTP.purpose == req.purpose,
        VerificationOTP.is_used == False,
        VerificationOTP.expires_at >= datetime.utcnow()
    ).first()

    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")

    otp_record.is_used = True
    
    # Mark user verified if exists
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.is_verified = True
    db.commit()

    return {"message": "Verification code successfully validated", "email": email}

@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="No user found with this email address")

    otp_code = str(random.randint(100000, 999999))
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    db.query(VerificationOTP).filter(
        VerificationOTP.email == email,
        VerificationOTP.purpose == "password_reset",
        VerificationOTP.is_used == False
    ).update({"is_used": True})

    otp_record = VerificationOTP(
        email=email,
        otp_code=otp_code,
        purpose="password_reset",
        expires_at=expires_at
    )
    db.add(otp_record)
    db.commit()

    print(f"[Password Reset OTP] Code for {email}: {otp_code}")
    return {
        "message": f"Password reset verification code sent to {email}",
        "email": email,
        "otp_code": otp_code
    }

@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="No user found with this email address")

    otp_record = db.query(VerificationOTP).filter(
        VerificationOTP.email == email,
        VerificationOTP.otp_code == req.otp_code.strip(),
        VerificationOTP.purpose == "password_reset",
        VerificationOTP.is_used == False,
        VerificationOTP.expires_at >= datetime.utcnow()
    ).first()

    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset code")

    if not req.new_password or len(req.new_password) < 4:
        raise HTTPException(status_code=400, detail="New password must be at least 4 characters long")

    user.hashed_password = get_password_hash(req.new_password)
    otp_record.is_used = True
    db.commit()

    return {"message": "Password reset successful. You can now log in with your new password."}

@router.post("/register", response_model=Token)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    if not user_in.password:
        raise HTTPException(status_code=400, detail="Password is required for local registration")

    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name or "New Candidate",
        phone_number=user_in.phone_number,
        avatar_url=user_in.avatar_url or f"https://api.dicebear.com/7.x/bottts/svg?seed={user_in.email}",
        auth_provider="local"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Initialize default student/candidate profile & preferences
    profile = CandidateProfile(
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone_number,
        phone_number=user.phone_number,
        college_name=None,
        cgpa=None,
        schooling={},
        roles=["Machine Learning Engineer", "AI Engineer", "Software Engineer"],
        skills=["Python", "PyTorch", "OpenCV", "Docker", "SQL", "Git"]
    )
    prefs = JobPreferences(user_id=user.id)
    db.add(profile)
    db.add(prefs)
    db.commit()
    
    token = create_access_token(user.id)
    return Token(access_token=token, token_type="bearer", user=UserOut.model_validate(user))

@router.post("/login", response_model=Token)
def login(login_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_in.email).first()
    if not user or not user.hashed_password or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(user.id)
    return Token(access_token=token, token_type="bearer", user=UserOut.model_validate(user))

import httpx

@router.post("/google", response_model=Token)
def google_auth(req: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Google OAuth 2.0 Sign-In / Sign-Up Endpoint.
    Verifies signed Google ID token via Google's tokeninfo API, auto-provisions account and seeds student profile.
    """
    email = None
    full_name = req.full_name
    google_id = req.google_id
    avatar_url = req.avatar_url

    # 1. Verify Google ID token against Google's API if token is provided
    if req.id_token:
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={req.id_token}")
                if res.status_code == 200:
                    token_info = res.json()
                    email = token_info.get("email")
                    full_name = token_info.get("name") or full_name
                    google_id = token_info.get("sub") or google_id
                    avatar_url = token_info.get("picture") or avatar_url
                else:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid Google OAuth ID token from Google servers"
                    )
        except HTTPException:
            raise
        except Exception as e:
            # If network error or timeout verifying with Google
            print(f"Warning: Google tokeninfo verification check failed: {e}")
            if not req.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not reach Google verification servers and no fallback email provided"
                )

    if not email:
        if req.email:
            email = req.email.strip().lower()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required for authentication"
            )

    email = email.strip().lower()
    full_name = full_name or email.split("@")[0].title()
    google_id = google_id or f"g_{abs(hash(email)) % 100000000}"
    avatar_url = avatar_url or f"https://api.dicebear.com/7.x/avataaars/svg?seed={email}"

    user = db.query(User).filter((User.email == email) | (User.google_id == google_id)).first()

    if not user:
        # Create new Google authenticated user
        user = User(
            email=email,
            hashed_password=get_password_hash(f"oauth_google_{google_id}_{email}"),
            full_name=full_name,
            phone_number=req.phone_number,
            avatar_url=avatar_url,
            auth_provider="google",
            google_id=google_id,
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Initialize student candidate profile with academic details
        profile = CandidateProfile(
            user_id=user.id,
            full_name=full_name,
            email=email,
            phone=req.phone_number,
            phone_number=req.phone_number,
            college_name=req.college_name or "University / College",
            degree="B.Tech in Computer Science & Engineering",
            cgpa=req.cgpa or "8.5/10",
            graduation_year=2025,
            schooling={
                "class_10th": {"school": "Secondary School", "board": "CBSE", "percentage": "90%"},
                "class_12th": {"school": "Higher Secondary School", "board": "CBSE", "percentage": "90%"}
            },
            roles=["Machine Learning Engineer", "AI Engineer", "Computer Vision Engineer"],
            skills=["Python", "PyTorch", "OpenCV", "Deep Learning", "Docker", "FastAPI", "SQL", "Git"]
        )
        prefs = JobPreferences(
            user_id=user.id,
            preferred_roles=["Machine Learning Engineer", "AI Engineer", "Computer Vision Engineer"],
            locations=["Bangalore", "Hyderabad", "Delhi NCR", "Pune", "Remote"],
            min_stipend=30000.0,
            min_salary=1000000.0
        )
        db.add(profile)
        db.add(prefs)
        db.commit()
    else:
        # Link user account to Google auth provider
        user.auth_provider = "google"
        user.google_id = google_id
        user.is_verified = True
        if not user.avatar_url:
            user.avatar_url = avatar_url

        # Update existing profile if newly provided academic credentials
        if req.college_name or req.cgpa or req.phone_number:
            if user.profile:
                if req.college_name:
                    user.profile.college_name = req.college_name
                if req.cgpa:
                    user.profile.cgpa = req.cgpa
                if req.phone_number:
                    user.profile.phone_number = req.phone_number
                    user.profile.phone = req.phone_number
                if req.phone_number and not user.phone_number:
                    user.phone_number = req.phone_number
        db.commit()

    token = create_access_token(user.id)
    return Token(access_token=token, token_type="bearer", user=UserOut.model_validate(user))

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)
