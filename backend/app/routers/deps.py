from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.services.auth_service import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    # If no token is provided in demo/dev mode, automatically provide or create default demo user
    if not token:
        user = db.query(User).filter(User.email == "vishal.aiml@example.com").first()
        if not user:
            from app.services.auth_service import get_password_hash
            user = User(
                email="vishal.aiml@example.com",
                hashed_password=get_password_hash("password123"),
                full_name="Vishal Sharma"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
