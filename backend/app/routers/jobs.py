from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Job, JobRequirement, JobSource, Company
from app.schemas import JobOut
from app.services.job_sources.seed_feed import SeedFeedSource
from app.services.job_sources.greenhouse_source import GreenhouseSource
from app.services.job_sources.remoteok_source import RemoteOKSource
from app.services.job_sources.linkedin_source import LinkedInSource
from app.services.job_sources.bangalore_startups_source import BangaloreStartupsSource
from app.services.job_sources.indian_startup_map_source import IndianStartupMapSource
from app.services.job_sources.delhi_startup_map_source import DelhiStartupMapSource
from app.services.deduplicator import generate_dedup_fingerprint, is_duplicate

router = APIRouter(prefix="/jobs", tags=["Jobs & Ingestion"])

async def run_job_ingestion(db: Session):
    sources = [
        SeedFeedSource(),
        BangaloreStartupsSource(),
        DelhiStartupMapSource(),
        IndianStartupMapSource(),
        LinkedInSource(),
        GreenhouseSource(),
        RemoteOKSource()
    ]
    
    total_fetched = 0
    total_new = 0
    total_duplicates = 0
    
    # Cache existing active jobs for fuzzy similarity
    existing_jobs = db.query(Job).filter(Job.is_active == True).all()
    
    for source in sources:
        # Register or get source
        source_record = db.query(JobSource).filter(JobSource.name == source.name).first()
        if not source_record:
            source_record = JobSource(name=source.name, source_type=source.source_type)
            db.add(source_record)
            db.commit()
            db.refresh(source_record)
            
        try:
            fetched_jobs = await source.fetch_jobs()
            total_fetched += len(fetched_jobs)
            
            for norm_job in fetched_jobs:
                fingerprint = generate_dedup_fingerprint(
                    norm_job.company_name, norm_job.title, norm_job.location
                )
                
                # Check exact fingerprint duplicate
                dup_job = db.query(Job).filter(Job.dedup_fingerprint == fingerprint).first()
                
                # Check fuzzy description/title duplicate
                if not dup_job:
                    for ej in existing_jobs:
                        if is_duplicate(
                            norm_job.title, norm_job.company_name, norm_job.description,
                            ej.title, ej.company_name, ej.description
                        ):
                            dup_job = ej
                            break
                            
                if dup_job:
                    total_duplicates += 1
                    continue
                    
                # Create Company if needed
                company = db.query(Company).filter(Company.name == norm_job.company_name).first()
                if not company:
                    company = Company(name=norm_job.company_name)
                    db.add(company)
                    db.commit()
                    db.refresh(company)
                    
                # Create Job
                job = Job(
                    source_id=source_record.id,
                    company_id=company.id,
                    external_id=norm_job.external_id,
                    company_name=norm_job.company_name,
                    title=norm_job.title,
                    description=norm_job.description,
                    location=norm_job.location,
                    remote_type=norm_job.remote_type,
                    salary_min=norm_job.salary_min,
                    salary_max=norm_job.salary_max,
                    stipend=norm_job.stipend,
                    currency=norm_job.currency,
                    employment_type=norm_job.employment_type,
                    experience_level=norm_job.experience_level,
                    min_experience_years=norm_job.min_experience_years,
                    application_url=norm_job.application_url,
                    posted_at=norm_job.posted_at,
                    deadline=norm_job.deadline,
                    dedup_fingerprint=fingerprint,
                    is_active=True
                )
                db.add(job)
                db.commit()
                db.refresh(job)
                
                # Create Job Requirement
                req = JobRequirement(
                    job_id=job.id,
                    role_category=norm_job.role_category,
                    required_skills=norm_job.required_skills,
                    preferred_skills=norm_job.preferred_skills,
                    nice_to_have_skills=norm_job.nice_to_have_skills,
                    responsibilities=norm_job.responsibilities,
                    education_requirement=norm_job.education_requirement,
                    experience_years_required=norm_job.min_experience_years
                )
                db.add(req)
                db.commit()
                
                existing_jobs.append(job)
                total_new += 1
                
            source_record.last_success = datetime.utcnow()
            source_record.jobs_count = db.query(Job).filter(Job.source_id == source_record.id).count()
            db.commit()
        except Exception as e:
            source_record.last_failure = datetime.utcnow()
            db.commit()
            print(f"Error ingesting source {source.name}: {e}")

    return {
        "fetched": total_fetched,
        "new_inserted": total_new,
        "duplicates_filtered": total_duplicates
    }

@router.get("", response_model=List[JobOut])
def list_jobs(
    q: Optional[str] = None,
    location: Optional[str] = None,
    employment_type: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(Job).filter(Job.is_active == True)
    if q:
        query = query.filter(Job.title.ilike(f"%{q}%") | Job.company_name.ilike(f"%{q}%"))
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    if employment_type:
        query = query.filter(Job.employment_type == employment_type)
        
    jobs = query.order_by(Job.posted_at.desc()).limit(limit).all()
    
    # Convert with source_name
    result = []
    for j in jobs:
        j_dict = {
            "id": j.id,
            "source_name": j.source.name if j.source else "Direct",
            "company_name": j.company_name,
            "title": j.title,
            "description": j.description,
            "location": j.location,
            "remote_type": j.remote_type,
            "salary_min": j.salary_min,
            "salary_max": j.salary_max,
            "stipend": j.stipend,
            "currency": j.currency,
            "employment_type": j.employment_type,
            "experience_level": j.experience_level,
            "min_experience_years": j.min_experience_years,
            "application_url": j.application_url,
            "posted_at": j.posted_at,
            "is_active": j.is_active,
            "requirements": j.requirements
        }
        result.append(j_dict)
    return result

@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": job.id,
        "source_name": job.source.name if job.source else "Direct",
        "company_name": job.company_name,
        "title": job.title,
        "description": job.description,
        "location": job.location,
        "remote_type": job.remote_type,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "stipend": job.stipend,
        "currency": job.currency,
        "employment_type": job.employment_type,
        "experience_level": job.experience_level,
        "min_experience_years": job.min_experience_years,
        "application_url": job.application_url,
        "posted_at": job.posted_at,
        "is_active": job.is_active,
        "requirements": job.requirements
    }

@router.post("/sync")
async def sync_jobs(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Triggers multi-source ingestion, normalization, and deduplication."""
    res = await run_job_ingestion(db)
    return {"message": "Job discovery sync completed", "stats": res}
