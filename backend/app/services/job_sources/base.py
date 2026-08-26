from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

class NormalizedJob(BaseModel):
    source_name: str
    external_id: Optional[str] = None
    company_name: str
    title: str
    description: str
    location: str = "Remote"
    remote_type: str = "on-site"  # remote, hybrid, on-site
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    stipend: Optional[float] = None
    currency: str = "INR"
    employment_type: str = "Full-time"  # Internship, Full-time, Contract, Part-time
    experience_level: str = "Entry-level"  # Fresher, 0-1 years, 1-2 years, Mid-level, Senior
    min_experience_years: float = 0.0
    application_url: str
    posted_at: datetime = datetime.utcnow()
    deadline: Optional[datetime] = None
    
    # Extracted Requirements
    role_category: Optional[str] = None
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    nice_to_have_skills: List[str] = []
    responsibilities: List[str] = []
    education_requirement: Optional[str] = None

class BaseJobSource(ABC):
    def __init__(self, name: str, source_type: str, base_url: Optional[str] = None):
        self.name = name
        self.source_type = source_type
        self.base_url = base_url

    @abstractmethod
    async def fetch_jobs(self) -> List[NormalizedJob]:
        """Fetch and normalize jobs from this source."""
        pass
