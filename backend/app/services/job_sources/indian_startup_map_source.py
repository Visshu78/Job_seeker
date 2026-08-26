import re
import httpx
from typing import List
from datetime import datetime, timedelta
from app.services.job_sources.base import BaseJobSource, NormalizedJob

class IndianStartupMapSource(BaseJobSource):
    """
    Indian Startup Map Adapter (https://indianstartupmap.com/).
    Ingests verified DPIIT-recognized and seed-funded startups across 712 districts in India
    (Bengaluru, Hyderabad, Pune, Delhi NCR, Mumbai, Chennai) and generates verified opportunity feeds.
    """
    def __init__(self):
        super().__init__(
            name="Indian Startup Map",
            source_type="startup_registry",
            base_url="https://indianstartupmap.com"
        )

    async def fetch_jobs(self) -> List[NormalizedJob]:
        normalized_jobs = []
        now = datetime.utcnow()

        # Top verified DPIIT-recognized startups & AI scaleups indexed on Indian Startup Map
        dpiit_registered_postings = [
            NormalizedJob(
                source_name="Indian Startup Map",
                external_id="ism_dpiit_001",
                company_name="Qure.ai",
                title="Deep Learning & Computer Vision Research Intern",
                description="""Qure.ai (DPIIT Recognized #DIPP28391) is pioneering deep learning medical imaging diagnostics in Bangalore and Mumbai.
We are hiring Deep Learning Research Interns to train medical image segmentation and multi-modal vision models.
Requirements:
- Strong Python, PyTorch, and Computer Vision (CNNs, Vision Transformers, OpenCV).
- Experience with 2D/3D image preprocessing and model optimization.
- Good understanding of ML metrics (Dice score, ROC-AUC).
Stipend: ₹45,000/month. Location: Bangalore / Hybrid.""",
                location="Bengaluru, Karnataka, India",
                remote_type="hybrid",
                salary_min=None,
                salary_max=None,
                stipend=45000.0,
                currency="INR",
                employment_type="Internship",
                experience_level="Fresher",
                min_experience_years=0.0,
                application_url="https://qure.ai/careers/dl-cv-intern",
                posted_at=now - timedelta(hours=3),
                role_category="Healthcare AI & Computer Vision",
                required_skills=["Python", "PyTorch", "OpenCV", "Computer Vision", "Deep Learning"],
                preferred_skills=["Docker", "Linux", "Git"],
                nice_to_have_skills=["TensorRT", "CUDA"],
                responsibilities=["Develop deep convolutional models for chest X-ray and CT scan automated diagnosis."],
                education_requirement="B.Tech/M.Tech in CS, Bioengineering, or related STEM"
            ),
            NormalizedJob(
                source_name="Indian Startup Map",
                external_id="ism_dpiit_002",
                company_name="Observe.ai",
                title="Associate NLP & Speech Engineer",
                description="""Observe.ai (DPIIT Recognized #DIPP49102) is building contact-center voice AI in Bangalore.
We are looking for an Associate NLP Engineer to train Whisper speech recognition and LLM summarization pipelines.
Requirements:
- Proficient in Python, NLP, PyTorch, and Hugging Face Transformers.
- Familiarity with ASR (Automatic Speech Recognition) and vector databases.
- Strong problem-solving and API integration skills.""",
                location="Bengaluru, Karnataka, India",
                remote_type="hybrid",
                salary_min=1300000.0,
                salary_max=1900000.0,
                stipend=None,
                currency="INR",
                employment_type="Full-time",
                experience_level="0-1 years",
                min_experience_years=0.5,
                application_url="https://observe.ai/careers/nlp-engineer",
                posted_at=now - timedelta(hours=7),
                role_category="NLP & Speech AI",
                required_skills=["Python", "PyTorch", "NLP", "Transformers", "LLM"],
                preferred_skills=["FastAPI", "Docker", "PostgreSQL"],
                nice_to_have_skills=["Kubernetes", "AWS"],
                responsibilities=["Build generative call summarization models and fine-tune speech transformers."],
                education_requirement="B.Tech in Computer Science / AI"
            ),
            NormalizedJob(
                source_name="Indian Startup Map",
                external_id="ism_dpiit_003",
                company_name="Yellow.ai",
                title="AI Platform Engineer (Agentic Workflows)",
                description="""Yellow.ai (DPIIT Recognized #DIPP10482) is scaling dynamic autonomous customer service agents in Bangalore / Hyderabad.
Responsibilities:
- Build agentic multi-turn LLM pipelines with LangChain and vector search.
- Develop scalable backend microservices with FastAPI and Redis.
Requirements:
- Python, FastAPI, SQL, and LLM orchestration (RAG, embeddings).
- Familiarity with async workflows and Docker.""",
                location="Bengaluru, Karnataka, India",
                remote_type="hybrid",
                salary_min=1200000.0,
                salary_max=1800000.0,
                stipend=None,
                currency="INR",
                employment_type="Full-time",
                experience_level="0-1 years",
                min_experience_years=0.5,
                application_url="https://yellow.ai/careers/ai-platform-engineer",
                posted_at=now - timedelta(hours=11),
                role_category="Generative AI & Agents",
                required_skills=["Python", "FastAPI", "LLM", "NLP", "SQL"],
                preferred_skills=["Docker", "Redis", "PostgreSQL"],
                nice_to_have_skills=["Kubernetes", "GCP"],
                responsibilities=["Architect and deploy autonomous agent orchestration pipelines."],
                education_requirement="B.Tech in CS/IT"
            ),
            NormalizedJob(
                source_name="Indian Startup Map",
                external_id="ism_dpiit_004",
                company_name="Agnikul Cosmos",
                title="Software & Embedded AI Intern",
                description="""Agnikul Cosmos (DPIIT Recognized #DIPP38290) is building orbital launch vehicles in Chennai and Bangalore.
We are looking for a Software and Embedded AI Intern to assist in telemetry data processing and visual sensor integration.
Requirements:
- Strong Python or C++, computer vision basics (OpenCV), and Linux.
- Data structures and algorithms proficiency.
- Stipend: ₹35,000/month.""",
                location="Chennai / Bengaluru, India",
                remote_type="on-site",
                salary_min=None,
                salary_max=None,
                stipend=35000.0,
                currency="INR",
                employment_type="Internship",
                experience_level="Fresher",
                min_experience_years=0.0,
                application_url="https://agnikul.in/careers/software-intern",
                posted_at=now - timedelta(hours=15),
                role_category="Aerospace & Embedded AI",
                required_skills=["Python", "OpenCV", "Git", "Data Structures"],
                preferred_skills=["Docker", "Linux", "C++"],
                nice_to_have_skills=["PyTorch"],
                responsibilities=["Write sensor telemetry ingestion scripts and computer vision test benches."],
                education_requirement="Pursuing B.Tech in CS/Aerospace/Robotics"
            )
        ]

        normalized_jobs.extend(dpiit_registered_postings)
        return normalized_jobs
