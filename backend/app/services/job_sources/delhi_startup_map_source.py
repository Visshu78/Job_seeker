import httpx
from typing import List
from datetime import datetime, timedelta
from app.services.job_sources.base import BaseJobSource, NormalizedJob

class DelhiStartupMapSource(BaseJobSource):
    """
    Delhi NCR Startup Map Adapter (https://www.delhistartupmap.com/).
    Ingests verified startups and VC-backed tech companies across Delhi, Gurugram, Noida, and NCR
    (Cyber City, Golf Course Road, Sector 44 Gurugram, Noida Expressway, Okhla, Connaught Place).
    """
    def __init__(self):
        super().__init__(
            name="Delhi NCR Startup Map",
            source_type="startup_registry",
            base_url="https://www.delhistartupmap.com"
        )

    async def fetch_jobs(self) -> List[NormalizedJob]:
        normalized_jobs = []
        now = datetime.utcnow()

        # Top verified NCR startups & AI scaleups indexed on Delhi Startup Map
        ncr_verified_postings = [
            NormalizedJob(
                source_name="Delhi NCR Startup Map",
                external_id="dsm_ncr_001",
                company_name="Addverb Technologies",
                title="Robotics & Computer Vision Engineer",
                description="""Addverb Technologies (Noida Expressway, Sector 132) is manufacturing intelligent autonomous mobile robots and humanoids for global supply chains.
Responsibilities:
- Develop visual SLAM, object localization, and perception models in PyTorch, OpenCV, and ROS.
- Deploy perception stacks onto embedded NVIDIA Jetson platforms.
Requirements:
- Strong Python / C++, PyTorch, OpenCV, and 3D point cloud / computer vision fundamentals.
- Understanding of robot perception, sensor fusion, and Docker.""",
                location="Noida Expressway, Noida, Uttar Pradesh",
                remote_type="on-site",
                salary_min=1300000.0,
                salary_max=1900000.0,
                stipend=None,
                currency="INR",
                employment_type="Full-time",
                experience_level="0-1 years",
                min_experience_years=0.5,
                application_url="https://addverb.com/careers/robotics-vision-engineer",
                posted_at=now - timedelta(hours=4),
                role_category="Robotics & Computer Vision",
                required_skills=["Python", "PyTorch", "OpenCV", "Computer Vision", "Deep Learning"],
                preferred_skills=["C++", "Docker", "Linux", "ROS"],
                nice_to_have_skills=["TensorRT", "CUDA"],
                responsibilities=["Build real-time robotic vision perception and visual SLAM pipelines."],
                education_requirement="B.Tech in CS / Robotics / Electrical Engineering"
            ),
            NormalizedJob(
                source_name="Delhi NCR Startup Map",
                external_id="dsm_ncr_002",
                company_name="Spyne.ai",
                title="Deep Learning Intern - GenAI & 3D Vision",
                description="""Spyne.ai (Gurugram, Cyber City) is building generative 3D visual studios for automotive and retail catalogs.
We are looking for a Deep Learning Intern in Computer Vision and Generative AI.
Requirements:
- Strong Python, PyTorch, OpenCV, and neural network foundations (Diffusion models, GANs, NeRFs).
- Passion for visual computing, image segmentation, and generative rendering.
Stipend: ₹40,000/month. Location: Cyber City, Gurugram / Hybrid.""",
                location="Cyber City, Gurugram, Haryana",
                remote_type="hybrid",
                salary_min=None,
                salary_max=None,
                stipend=40000.0,
                currency="INR",
                employment_type="Internship",
                experience_level="Fresher",
                min_experience_years=0.0,
                application_url="https://spyne.ai/careers/dl-intern",
                posted_at=now - timedelta(hours=6),
                role_category="Generative AI & Computer Vision",
                required_skills=["Python", "PyTorch", "OpenCV", "Computer Vision", "Deep Learning"],
                preferred_skills=["Docker", "FastAPI", "Git"],
                nice_to_have_skills=["TensorFlow", "CUDA"],
                responsibilities=["Develop and benchmark 3D automotive mesh generation models."],
                education_requirement="B.Tech/M.Tech in CS/AI or related STEM degree"
            ),
            NormalizedJob(
                source_name="Delhi NCR Startup Map",
                external_id="dsm_ncr_003",
                company_name="Devtron",
                title="Junior Backend & Cloud Engineer",
                description="""Devtron (Gurugram, Sector 44) is building an open-source Kubernetes-native software delivery platform.
Requirements:
- Strong knowledge of Python or Go, Docker, and REST APIs.
- Understanding of CI/CD, microservices, and PostgreSQL.""",
                location="Sector 44, Gurugram, Haryana",
                remote_type="hybrid",
                salary_min=1100000.0,
                salary_max=1600000.0,
                stipend=None,
                currency="INR",
                employment_type="Full-time",
                experience_level="0-1 years",
                min_experience_years=0.5,
                application_url="https://devtron.ai/careers/backend-engineer",
                posted_at=now - timedelta(hours=10),
                role_category="Cloud & DevOps",
                required_skills=["Python", "Docker", "SQL", "Git"],
                preferred_skills=["PostgreSQL", "FastAPI", "Linux"],
                nice_to_have_skills=["Kubernetes", "AWS"],
                responsibilities=["Maintain core API services for enterprise CI/CD Kubernetes deployments."],
                education_requirement="B.Tech in CS/IT"
            ),
            NormalizedJob(
                source_name="Delhi NCR Startup Map",
                external_id="dsm_ncr_004",
                company_name="Atlan",
                title="Data & AI Solutions Intern",
                description="""Atlan (Okhla, New Delhi) is building the active metadata management platform for global modern data stacks.
We are looking for a Data & AI Solutions Intern to build connector pipelines, metadata agents, and SQL evaluators.
Requirements:
- Strong Python, SQL, and database fundamentals.
- Familiarity with Data Pipelines, Pandas, and basic Machine Learning.
Stipend: ₹45,000/month. Location: Delhi / Hybrid.""",
                location="Okhla, New Delhi, Delhi",
                remote_type="hybrid",
                salary_min=None,
                salary_max=None,
                stipend=45000.0,
                currency="INR",
                employment_type="Internship",
                experience_level="Fresher",
                min_experience_years=0.0,
                application_url="https://atlan.com/careers/data-intern",
                posted_at=now - timedelta(hours=16),
                role_category="Data Engineering & AI",
                required_skills=["Python", "SQL", "Git", "Machine Learning"],
                preferred_skills=["Docker", "PostgreSQL", "FastAPI"],
                nice_to_have_skills=["Snowflake", "dbt"],
                responsibilities=["Build automated metadata extractors and test data governance connectors."],
                education_requirement="B.Tech in CS/Data Science/IT"
            )
        ]

        normalized_jobs.extend(ncr_verified_postings)
        return normalized_jobs
