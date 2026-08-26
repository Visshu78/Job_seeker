import re
from typing import Dict, Any, List, Tuple, Set
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.config import settings

TRANSFERABLE_GRAPH = {
    "tensorflow": ("PyTorch", "Candidate has deep PyTorch expertise; core deep learning principles directly transfer."),
    "pytorch": ("TensorFlow", "Candidate has TensorFlow expertise; deep neural network concepts readily transfer."),
    "keras": ("PyTorch", "PyTorch deep learning experience transfers directly to Keras/TF."),
    "gcp": ("AWS", "Candidate has AWS cloud experience; IAM, compute, and storage patterns transfer smoothly to GCP."),
    "aws": ("GCP", "Candidate has GCP experience; cloud architecture concepts transfer to AWS."),
    "azure": ("AWS", "Cloud architectural foundations in AWS transfer to Azure."),
    "vue": ("React", "Solid React component and state management foundations transfer quickly to Vue."),
    "angular": ("React", "Component lifecycle and modern JS/TS patterns in React transfer to Angular."),
    "flask": ("FastAPI", "Modern async FastAPI experience encompasses standard WSGI/Flask patterns."),
    "django": ("FastAPI", "Backend REST and DB ORM experience in FastAPI transfers to Django."),
    "mysql": ("PostgreSQL", "Relational database and SQL proficiency in PostgreSQL directly transfers to MySQL."),
    "postgresql": ("MySQL", "Relational database and SQL proficiency transfers to PostgreSQL."),
    "scikit-learn": ("PyTorch", "Candidate demonstrates advanced ML/DL modeling with PyTorch."),
    "opencv": ("PyTorch", "Deep computer vision experience with PyTorch provides strong perceptual modeling background."),
    "kubernetes": ("Docker", "Candidate has containerization experience with Docker, easing container orchestration onboarding.")
}

CITY_SYNONYMS = {
    "bangalore": ["bangalore", "bengaluru"],
    "bengaluru": ["bangalore", "bengaluru"],
    "gurgaon": ["gurgaon", "gurugram", "delhi", "noida", "delhi ncr"],
    "gurugram": ["gurgaon", "gurugram", "delhi", "noida", "delhi ncr"],
    "delhi": ["delhi", "new delhi", "noida", "gurgaon", "delhi ncr"],
    "mumbai": ["mumbai", "bombay", "navi mumbai", "pune", "maharashtra"],
    "hyderabad": ["hyderabad", "secunderabad", "telangana"],
    "pune": ["pune", "maharashtra"],
    "india": ["india", "bangalore", "bengaluru", "hyderabad", "pune", "mumbai", "delhi", "noida", "gurgaon", "chennai", "kolkata"]
}

def hard_filter(job: Dict[str, Any], preferences: Dict[str, Any]) -> Tuple[bool, str]:
    job_loc = (job.get("location") or "").lower()
    job_remote = (job.get("remote_type") or "").lower()
    pref_locs = [l.lower() for l in preferences.get("locations", [])]
    pref_remote_only = preferences.get("remote_only", False)
    
    if pref_remote_only and "remote" not in job_remote and "remote" not in job_loc:
        return False, "Job is not remote as required by preferences"
        
    if "remote" not in job_remote and "remote" not in job_loc and pref_locs:
        # Expand user preferred locations with synonyms
        expanded_locs = set(pref_locs)
        for loc in pref_locs:
            for syn_key, syn_list in CITY_SYNONYMS.items():
                if syn_key in loc:
                    expanded_locs.update(syn_list)
                    
        loc_matched = any(c in job_loc for c in expanded_locs)
        if not loc_matched:
            return False, f"Location {job.get('location')} does not match preferred locations {pref_locs}"
            
    is_intern = "intern" in (job.get("employment_type") or "").lower() or "intern" in (job.get("title") or "").lower()
    if is_intern:
        pref_min_stipend = preferences.get("min_stipend", 0.0)
        job_stipend = job.get("stipend") or 0.0
        if job_stipend > 0 and job_stipend < pref_min_stipend:
            return False, f"Stipend ₹{job_stipend} below minimum threshold ₹{pref_min_stipend}"
    else:
        pref_min_sal = preferences.get("min_salary", 0.0)
        job_sal_min = job.get("salary_min") or 0.0
        if job_sal_min > 0 and job_sal_min < pref_min_sal:
            return False, f"Salary ₹{job_sal_min} below minimum threshold ₹{pref_min_sal}"
            
    excluded = [c.lower() for c in preferences.get("excluded_companies", [])]
    job_comp = (job.get("company_name") or "").lower()
    if any(ex in job_comp for ex in excluded):
        return False, f"Company {job.get('company_name')} is in excluded list"
        
    return True, "Passed hard filters"


def compute_skill_matching(
    candidate_skills: List[str],
    required_skills: List[str],
    preferred_skills: List[str],
    nice_to_have_skills: List[str]
) -> Dict[str, Any]:
    c_skills_lower = {s.lower(): s for s in candidate_skills}
    
    matched = []
    missing = []
    transferable = []
    partial = []
    
    total_weight = 0.0
    earned_weight = 0.0
    
    for req in required_skills:
        req_l = req.lower()
        total_weight += 1.0
        if req_l in c_skills_lower:
            matched.append({"skill": c_skills_lower[req_l], "type": "REQUIRED"})
            earned_weight += 1.0
        elif req_l in TRANSFERABLE_GRAPH and TRANSFERABLE_GRAPH[req_l][0].lower() in c_skills_lower:
            from_skill, reason = TRANSFERABLE_GRAPH[req_l]
            transferable.append({
                "required": req,
                "candidate_has": c_skills_lower.get(from_skill.lower(), from_skill),
                "type": "REQUIRED",
                "explanation": reason
            })
            earned_weight += 0.85
        else:
            missing.append({"skill": req, "type": "REQUIRED", "severity": "HIGH"})

    for pref in preferred_skills:
        pref_l = pref.lower()
        total_weight += 0.6
        if pref_l in c_skills_lower:
            matched.append({"skill": c_skills_lower[pref_l], "type": "PREFERRED"})
            earned_weight += 0.6
        elif pref_l in TRANSFERABLE_GRAPH and TRANSFERABLE_GRAPH[pref_l][0].lower() in c_skills_lower:
            from_skill, reason = TRANSFERABLE_GRAPH[pref_l]
            transferable.append({
                "required": pref,
                "candidate_has": c_skills_lower.get(from_skill.lower(), from_skill),
                "type": "PREFERRED",
                "explanation": reason
            })
            earned_weight += 0.5
        else:
            missing.append({"skill": pref, "type": "PREFERRED", "severity": "MEDIUM"})

    for nth in nice_to_have_skills:
        nth_l = nth.lower()
        total_weight += 0.3
        if nth_l in c_skills_lower:
            matched.append({"skill": c_skills_lower[nth_l], "type": "NICE_TO_HAVE"})
            earned_weight += 0.3
        else:
            missing.append({"skill": nth, "type": "NICE_TO_HAVE", "severity": "LOW"})

    skill_score = (earned_weight / total_weight * 100.0) if total_weight > 0 else 85.0
    
    return {
        "score": round(float(min(100.0, max(0.0, skill_score))), 1),
        "matched": matched,
        "missing": missing,
        "transferable": transferable,
        "partial": partial
    }


def compute_semantic_similarity(resume_text: str, job_text: str) -> float:
    if not resume_text or not job_text:
        return 82.0
    try:
        tfidf = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        matrix = tfidf.fit_transform([resume_text, job_text])
        sim = float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
        scaled_score = 65.0 + (sim * 45.0)
        return round(float(min(98.0, max(50.0, scaled_score))), 1)
    except Exception:
        return 82.0


def evaluate_job_match(
    candidate_profile: Dict[str, Any],
    job: Dict[str, Any],
    preferences: Dict[str, Any],
    resume_raw_text: str = ""
) -> Dict[str, Any]:
    reqs = job.get("requirements") or {}
    req_skills = reqs.get("required_skills", []) or []
    pref_skills = reqs.get("preferred_skills", []) or []
    nth_skills = reqs.get("nice_to_have_skills", []) or []
    
    c_skills = candidate_profile.get("skills", [])
    
    skill_res = compute_skill_matching(c_skills, req_skills, pref_skills, nth_skills)
    skill_score = skill_res["score"]
    
    profile_text = f"{candidate_profile.get('summary', '')} {' '.join(c_skills)} {' '.join([p.get('title', '') + ' ' + p.get('description', '') for p in candidate_profile.get('projects', [])])} {resume_raw_text}"
    job_text = f"{job.get('title', '')} {job.get('company_name', '')} {job.get('description', '')}"
    semantic_score = compute_semantic_similarity(profile_text, job_text)
    
    job_min_exp = job.get("min_experience_years", 0.0) or 0.0
    cand_exp = candidate_profile.get("years_of_experience", 0.0) or 0.5
    if cand_exp >= job_min_exp:
        experience_score = 95.0
    elif (job_min_exp - cand_exp) <= 0.5:
        experience_score = 82.0
    else:
        experience_score = 65.0

    pref_score = 92.0
    job_loc = (job.get("location") or "").lower()
    pref_locs = [l.lower() for l in preferences.get("locations", [])]
    if "remote" in job_loc or any(p in job_loc for p in pref_locs):
        pref_score += 5.0
    else:
        pref_score -= 10.0
    preference_score = round(float(min(100.0, max(50.0, pref_score))), 1)
    
    cand_roles = [r.lower() for r in (candidate_profile.get("roles") or [])]
    pref_roles = [r.lower() for r in (preferences.get("preferred_roles") or [])]
    job_title = (job.get("title") or "").lower()
    
    role_matched = any(r in job_title or job_title in r for r in (cand_roles + pref_roles))
    role_score = 95.0 if role_matched else 78.0
    
    edu_score = 92.0
    
    overall_score = (
        settings.WEIGHT_SKILL * skill_score +
        settings.WEIGHT_SEMANTIC * semantic_score +
        settings.WEIGHT_EXPERIENCE * experience_score +
        settings.WEIGHT_PREFERENCE * preference_score +
        settings.WEIGHT_ROLE * role_score +
        settings.WEIGHT_EDUCATION * edu_score
    )
    overall_score = round(float(min(99.0, max(30.0, overall_score))), 1)
    
    if overall_score >= settings.HIGH_PRIORITY_THRESHOLD:
        tier = "HIGH_PRIORITY"
    elif overall_score >= settings.CONSIDER_THRESHOLD:
        tier = "CONSIDER"
    else:
        tier = "LOW_PRIORITY"
        
    return {
        "overall_score": overall_score,
        "skill_score": skill_score,
        "semantic_score": semantic_score,
        "experience_score": experience_score,
        "preference_score": preference_score,
        "role_score": role_score,
        "education_score": edu_score,
        "recommendation_tier": tier,
        "matched_skills": skill_res["matched"],
        "missing_skills": skill_res["missing"],
        "transferable_skills": skill_res["transferable"],
        "partial_skills": skill_res["partial"]
    }
