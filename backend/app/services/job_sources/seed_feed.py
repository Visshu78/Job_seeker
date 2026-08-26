from typing import List
from datetime import datetime, timedelta
from app.services.job_sources.base import BaseJobSource, NormalizedJob

class SeedFeedSource(BaseJobSource):
    def __init__(self):
        super().__init__(name="AI Career Ingestion Hub", source_type="feed")

    async def fetch_jobs(self) -> List[NormalizedJob]:
        now = datetime.utcnow()
        return [
            # High-Match ML Opportunity 1 (Targeted to PRD Persona A - Bangalore ML Intern)
            NormalizedJob(
                source_name="Greenhouse",
                external_id="gh_seed_001",
                company_name="XYZ Labs AI",
                title="ML Engineer Intern",
                description="""XYZ Labs is seeking an ambitious Machine Learning Engineer Intern to join our Computer Vision and Generative AI research team in Bangalore.
You will build, evaluate, and deploy deep learning models using Python and PyTorch.
Key Responsibilities:
- Implement deep neural networks for visual perception and object detection.
- Optimize PyTorch models for edge and cloud deployment.
- Collaborate with senior AI researchers on innovative state-of-the-art architectures.
Requirements:
- Strong proficiency in Python, PyTorch, OpenCV, and Deep Learning fundamentals.
- Solid understanding of linear algebra and machine learning algorithms.
- Experience with Git and version control.
Preferred:
- Familiarity with Docker containerization and AWS cloud infrastructure.
- Exposure to Kubernetes or model serving frameworks (TorchServe, Triton).""",
                location="Bangalore",
                remote_type="hybrid",
                salary_min=None,
                salary_max=None,
                stipend=35000.0,
                currency="INR",
                employment_type="Internship",
                experience_level="Fresher",
                min_experience_years=0.0,
                application_url="https://boards.greenhouse.io/xyzlabs/jobs/4019283",
                posted_at=now - timedelta(hours=3),
                role_category="Machine Learning",
                required_skills=["Python", "PyTorch", "OpenCV", "Deep Learning", "Machine Learning"],
                preferred_skills=["Docker", "AWS"],
                nice_to_have_skills=["Kubernetes", "FastAPI"],
                responsibilities=[
                    "Implement deep neural networks for visual perception and object detection.",
                    "Optimize PyTorch models for inference.",
                    "Collaborate with AI researchers on state-of-the-art vision architectures."
                ],
                education_requirement="B.Tech/M.Tech in Computer Science, Data Science, or related STEM field"
            ),
            
            # Opportunity 2 - Computer Vision Engineer (Bangalore Full-time)
            NormalizedJob(
                source_name="Lever",
                external_id="lev_seed_002",
                company_name="VisionCraft AI",
                title="Computer Vision Engineer",
                description="""VisionCraft AI is building next-generation real-time video intelligence platforms. We are looking for an entry-level / junior Computer Vision Engineer based in Bangalore or Remote.
What You Will Do:
- Design real-time tracking, segmentation, and YOLO/transformer-based object detection pipelines.
- Integrate OpenCV and PyTorch deep models with production streaming APIs.
- Benchmark and optimize inference latency.
Requirements:
- Hands-on experience in Python, OpenCV, PyTorch, and Computer Vision.
- Understanding of convolutional neural networks and transformer vision models.
Preferred:
- Experience with Docker, Linux, and REST APIs (FastAPI/Flask).
- Knowledge of TensorFlow or ONNX runtime.""",
                location="Bangalore",
                remote_type="hybrid",
                salary_min=1000000.0,
                salary_max=1600000.0,
                stipend=None,
                currency="INR",
                employment_type="Full-time",
                experience_level="0-1 years",
                min_experience_years=0.5,
                application_url="https://jobs.lever.co/visioncraft/5b39e2a1",
                posted_at=now - timedelta(hours=6),
                role_category="Computer Vision",
                required_skills=["Python", "PyTorch", "OpenCV", "Computer Vision", "Deep Learning"],
                preferred_skills=["Docker", "FastAPI", "Linux"],
                nice_to_have_skills=["TensorFlow", "Kubernetes", "AWS"],
                responsibilities=[
                    "Design real-time tracking and detection pipelines using YOLO and PyTorch.",
                    "Integrate OpenCV models into production services.",
                    "Optimize model latency and throughput."
                ],
                education_requirement="B.Tech in CS/IT/ECE"
            ),

            # Opportunity 3 - AI Engineer / LLM Applications (Hyderabad / Remote)
            NormalizedJob(
                source_name="Adzuna",
                external_id="adz_seed_003",
                company_name="Nexus Cognitive",
                title="AI Engineer - GenAI & RAG",
                description="""Nexus Cognitive is scaling enterprise agentic workflows and LLM applications. We are hiring an AI Engineer to join our Hyderabad team.
Responsibilities:
- Build Retrieval-Augmented Generation (RAG) systems using LangChain, vector databases (Qdrant/Pinecone), and Python.
- Fine-tune and evaluate open-source transformer models (LLaMA, Mistral).
- Develop robust FastAPI backends to serve AI pipelines.
Requirements:
- Proficient in Python, NLP, LLMs, and RAG architectures.
- Experience with embeddings, vector search, and Transformers (Hugging Face).
Preferred:
- Experience with Docker, PostgreSQL, and Cloud (AWS or GCP).""",
                location="Hyderabad",
                remote_type="remote",
                salary_min=900000.0,
                salary_max=1500000.0,
                stipend=None,
                currency="INR",
                employment_type="Full-time",
                experience_level="0-1 years",
                min_experience_years=0.5,
                application_url="https://nexus-cognitive.ai/careers/ai-engineer",
                posted_at=now - timedelta(hours=10),
                role_category="NLP & LLM",
                required_skills=["Python", "NLP", "LLM", "Transformers", "RAG", "LangChain"],
                preferred_skills=["FastAPI", "Docker", "PostgreSQL"],
                nice_to_have_skills=["AWS", "GCP", "Kubernetes"],
                responsibilities=[
                    "Build RAG systems using embeddings and vector search.",
                    "Fine-tune open-source models.",
                    "Expose model APIs with FastAPI."
                ],
                education_requirement="B.Tech / B.E. in CS/AI"
            ),

            # Opportunity 4 - Full-Stack AI Engineer (Remote)
            NormalizedJob(
                source_name="RemoteOK",
                external_id="rok_seed_004",
                company_name="HyperScale Systems",
                title="Full Stack Software Engineer (AI Platforms)",
                description="""HyperScale Systems is looking for a versatile Full Stack Developer to build UI and backend interfaces for our AI model management suite.
Requirements:
- Strong frontend proficiency in React, Next.js, TypeScript, and modern CSS/Tailwind.
- Robust backend development experience in Python (FastAPI/Django) or Node.js.
- Understanding of PostgreSQL, Redis, and Docker.
Preferred:
- Basic awareness of Machine Learning workflows and LLM APIs.
- Experience in CI/CD and automated testing.""",
                location="Remote",
                remote_type="remote",
                salary_min=1100000.0,
                salary_max=1800000.0,
                stipend=None,
                currency="INR",
                employment_type="Full-time",
                experience_level="1-2 years",
                min_experience_years=1.0,
                application_url="https://remoteok.com/l/hyperscale-fullstack",
                posted_at=now - timedelta(hours=14),
                role_category="Full Stack",
                required_skills=["React", "Next.js", "TypeScript", "Python", "FastAPI", "PostgreSQL"],
                preferred_skills=["Docker", "Redis", "Tailwind"],
                nice_to_have_skills=["AWS", "GraphQL"],
                responsibilities=[
                    "Develop intuitive frontend interfaces in React and Next.js.",
                    "Implement scalable backend APIs in FastAPI.",
                    "Manage database migrations and state management."
                ],
                education_requirement="B.Tech/B.S. in Computer Science"
            ),

            # Opportunity 5 - Software Engineering Intern (Pune / Hybrid)
            NormalizedJob(
                source_name="Greenhouse",
                external_id="gh_seed_005",
                company_name="Apex Data Cloud",
                title="Software Engineering Intern",
                description="""Join Apex Data Cloud as an engineering intern. Work on distributed systems, data processing pipelines, and RESTful APIs.
Requirements:
- Good understanding of Python or Java.
- Data structures and algorithms proficiency.
- Basic SQL and Git familiarity.
Stipend: ₹30,000/month. Location: Pune.""",
                location="Pune",
                remote_type="hybrid",
                salary_min=None,
                salary_max=None,
                stipend=30000.0,
                currency="INR",
                employment_type="Internship",
                experience_level="Fresher",
                min_experience_years=0.0,
                application_url="https://boards.greenhouse.io/apexdata/jobs/839102",
                posted_at=now - timedelta(hours=18),
                role_category="Software Engineering",
                required_skills=["Python", "SQL", "Git", "Data Structures"],
                preferred_skills=["Docker", "Linux"],
                nice_to_have_skills=["PostgreSQL", "FastAPI"],
                responsibilities=[
                    "Write modular and tested Python code.",
                    "Assist in designing backend microservices."
                ],
                education_requirement="Pursuing B.Tech/B.E. (Graduating 2025/2026)"
            ),

            # Opportunity 6 - Duplicate Intentional Seed to test Deduplication Engine
            # (Same role as #1 XYZ Labs posted on a partner board with slightly different title)
            NormalizedJob(
                source_name="Adzuna",
                external_id="adz_dup_006",
                company_name="XYZ Labs AI",
                title="Machine Learning Engineering Intern (Vision)",
                description="""XYZ Labs is hiring an ML Intern for Computer Vision and GenAI in Bangalore.
Build and deploy deep learning models using Python and PyTorch.
Requirements:
- Python, PyTorch, OpenCV, Deep Learning.""",
                location="Bangalore, Karnataka",
                remote_type="hybrid",
                salary_min=None,
                salary_max=None,
                stipend=35000.0,
                currency="INR",
                employment_type="Internship",
                experience_level="Fresher",
                min_experience_years=0.0,
                application_url="https://adzuna.in/land/ad/xyzlabs-intern-4019283",
                posted_at=now - timedelta(hours=2),
                role_category="Machine Learning",
                required_skills=["Python", "PyTorch", "OpenCV", "Deep Learning"],
                preferred_skills=["Docker", "AWS"],
                nice_to_have_skills=["Kubernetes"],
                responsibilities=["Implement deep neural networks."],
                education_requirement="B.Tech Computer Science"
            )
        ]
