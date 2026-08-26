import httpx
from typing import List
from datetime import datetime
from app.services.job_sources.base import BaseJobSource, NormalizedJob

class GreenhouseSource(BaseJobSource):
    def __init__(self, board_tokens: List[str] = None):
        super().__init__(name="Greenhouse", source_type="ats_api", base_url="https://boards-api.greenhouse.io/v1/boards/")
        self.board_tokens = board_tokens or ["figma", "databricks", "stripe", "scaleai"]

    async def fetch_jobs(self) -> List[NormalizedJob]:
        normalized_jobs = []
        async with httpx.AsyncClient(timeout=10.0) as client:
            for token in self.board_tokens:
                try:
                    url = f"{self.base_url}{token}/jobs?content=true"
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        data = resp.json()
                        company = token.capitalize()
                        for item in data.get("jobs", []):
                            title = item.get("title", "")
                            location = item.get("location", {}).get("name", "Remote")
                            content = item.get("content", "") or f"Exciting opportunity at {company} for {title}."
                            app_url = item.get("absolute_url", "")
                            ext_id = str(item.get("id"))
                            
                            is_remote = "remote" in location.lower() or "remote" in title.lower()
                            remote_type = "remote" if is_remote else "hybrid" if "hybrid" in location.lower() else "on-site"
                            
                            emp_type = "Internship" if "intern" in title.lower() else "Full-time"
                            exp_level = "Fresher" if "intern" in title.lower() else "0-1 years" if "junior" in title.lower() or "entry" in title.lower() else "1-2 years"
                            
                            # Derive skills
                            req_skills = []
                            if any(k in title.lower() for k in ["machine learning", "ml", "ai"]):
                                req_skills = ["Python", "PyTorch", "Machine Learning"]
                            elif "frontend" in title.lower():
                                req_skills = ["React", "TypeScript", "JavaScript", "HTML", "CSS"]
                            elif "backend" in title.lower():
                                req_skills = ["Python", "PostgreSQL", "Docker", "REST API"]
                            else:
                                req_skills = ["Python", "Git", "SQL"]

                            normalized_jobs.append(NormalizedJob(
                                source_name="Greenhouse",
                                external_id=f"gh_{token}_{ext_id}",
                                company_name=company,
                                title=title,
                                description=content,
                                location=location,
                                remote_type=remote_type,
                                salary_min=1200000.0 if emp_type == "Full-time" else None,
                                salary_max=2400000.0 if emp_type == "Full-time" else None,
                                stipend=45000.0 if emp_type == "Internship" else None,
                                currency="INR" if "india" in location.lower() or "bangalore" in location.lower() else "USD",
                                employment_type=emp_type,
                                experience_level=exp_level,
                                min_experience_years=0.0 if emp_type == "Internship" else 1.0,
                                application_url=app_url or f"https://boards.greenhouse.io/{token}/jobs/{ext_id}",
                                posted_at=datetime.utcnow(),
                                role_category="AI / Engineering",
                                required_skills=req_skills,
                                preferred_skills=["Docker", "AWS", "FastAPI"],
                                nice_to_have_skills=["Kubernetes", "Redis"],
                                responsibilities=[f"Design and deploy production solutions at {company}."],
                                education_requirement="B.Tech / B.E. in Computer Science or related STEM field"
                            ))
                except Exception as e:
                    print(f"Greenhouse fetch error for {token}: {e}")
        return normalized_jobs
