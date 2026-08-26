import httpx
from typing import List
from datetime import datetime
from app.services.job_sources.base import BaseJobSource, NormalizedJob

class RemoteOKSource(BaseJobSource):
    def __init__(self):
        super().__init__(name="RemoteOK", source_type="job_board", base_url="https://remoteok.com/api")

    async def fetch_jobs(self) -> List[NormalizedJob]:
        normalized_jobs = []
        try:
            async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": "JobAgent/1.0"}) as client:
                resp = await client.get(self.base_url)
                if resp.status_code == 200:
                    data = resp.json()
                    # First element in remoteok is often metadata
                    postings = [p for p in data if isinstance(p, dict) and p.get("id")]
                    for item in postings[:25]:
                        title = item.get("position", "Software Engineer")
                        company = item.get("company", "Tech Company")
                        desc = item.get("description", "")
                        tags = item.get("tags", [])
                        app_url = item.get("url", f"https://remoteok.com/l/{item.get('id')}")
                        
                        salary_min = float(item.get("salary_min", 0)) if item.get("salary_min") else 800000.0
                        salary_max = float(item.get("salary_max", 0)) if item.get("salary_max") else 1600000.0

                        normalized_jobs.append(NormalizedJob(
                            source_name="RemoteOK",
                            external_id=f"remoteok_{item.get('id')}",
                            company_name=company,
                            title=title,
                            description=desc,
                            location="Remote (Global)",
                            remote_type="remote",
                            salary_min=salary_min,
                            salary_max=salary_max,
                            stipend=None,
                            currency="USD",
                            employment_type="Full-time",
                            experience_level="0-1 years" if "junior" in title.lower() else "1-2 years",
                            min_experience_years=1.0,
                            application_url=app_url,
                            posted_at=datetime.utcnow(),
                            role_category="Engineering",
                            required_skills=[t.capitalize() for t in tags[:4]] or ["Python", "JavaScript"],
                            preferred_skills=["Docker", "AWS", "Git"],
                            nice_to_have_skills=["PostgreSQL"],
                            responsibilities=["Collaborate across remote engineering teams to ship features."],
                            education_requirement="Bachelor's degree or equivalent practical experience"
                        ))
        except Exception as e:
            print(f"RemoteOK fetch error: {e}")
        return normalized_jobs
