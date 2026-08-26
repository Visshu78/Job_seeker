from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# If using SQLite, ensure check_same_thread is False
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

from sqlalchemy import text, inspect

def sync_database_schema():
    """Ensures newly added columns exist in existing SQLite/MySQL tables without dropping data."""
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        inspector = inspect(engine)
        
        # User columns
        user_cols = {col["name"] for col in inspector.get_columns("users")}
        if "phone_number" not in user_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN phone_number VARCHAR(100)"))
        if "avatar_url" not in user_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500)"))
        if "auth_provider" not in user_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN auth_provider VARCHAR(50) DEFAULT 'local'"))
        if "google_id" not in user_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN google_id VARCHAR(255)"))
        if "is_verified" not in user_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT 0"))

        # CandidateProfile columns
        profile_cols = {col["name"] for col in inspector.get_columns("candidate_profiles")}
        if "phone_number" not in profile_cols:
            conn.execute(text("ALTER TABLE candidate_profiles ADD COLUMN phone_number VARCHAR(100)"))
        if "college_name" not in profile_cols:
            conn.execute(text("ALTER TABLE candidate_profiles ADD COLUMN college_name VARCHAR(255)"))
        if "degree" not in profile_cols:
            conn.execute(text("ALTER TABLE candidate_profiles ADD COLUMN degree VARCHAR(100)"))
        if "cgpa" not in profile_cols:
            conn.execute(text("ALTER TABLE candidate_profiles ADD COLUMN cgpa VARCHAR(50)"))
        if "graduation_year" not in profile_cols:
            conn.execute(text("ALTER TABLE candidate_profiles ADD COLUMN graduation_year INTEGER"))
        if "schooling" not in profile_cols:
            conn.execute(text("ALTER TABLE candidate_profiles ADD COLUMN schooling JSON"))

        conn.commit()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
