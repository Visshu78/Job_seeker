from typing import Dict, Any, List
from datetime import datetime

def generate_cover_letter(
    candidate_profile: Dict[str, Any],
    job: Dict[str, Any],
    matched_skills: List[Dict[str, Any]]
) -> str:
    """Generates an honest, tailored cover letter based on verified candidate profile data."""
    cand_name = candidate_profile.get("full_name") or "Candidate"
    comp_name = job.get("company_name") or "Hiring Team"
    job_title = job.get("title") or "the position"
    skills_list = [m["skill"] for m in matched_skills[:4]]
    skills_str = ", ".join(skills_list) if skills_list else "software engineering and modern AI technologies"
    
    top_project = None
    if candidate_profile.get("projects"):
        top_project = candidate_profile.get("projects")[0]
        
    project_snippet = ""
    if top_project:
        project_snippet = f"In my recent project, '{top_project.get('title')}', I worked extensively with {', '.join(top_project.get('technologies', []))}, where I {top_project.get('description', '')[:120]}..."

    letter = f"""Dear Hiring Team at {comp_name},

I am writing to express my strong interest in the {job_title} role at {comp_name}. With my background in {skills_str}, I am excited about the opportunity to contribute to your team's ongoing initiatives.

{project_snippet}

What excites me most about {comp_name} is the opportunity to work on challenging engineering problems in a high-impact environment. My experience has prepared me to quickly ramp up, write clean and maintainable code, and collaborate effectively with team members.

Thank you for considering my application. I look forward to the possibility of discussing how my skills and background can add value to {comp_name}.

Sincerely,
{cand_name}
"""
    return letter.strip()


def generate_screening_answers(
    candidate_profile: Dict[str, Any],
    job: Dict[str, Any]
) -> Dict[str, str]:
    """Generates answers to common job screening questions based on candidate background."""
    comp_name = job.get("company_name") or "the company"
    job_title = job.get("title") or "this role"
    skills = candidate_profile.get("skills", [])
    
    return {
        f"Why are you interested in joining {comp_name}?": 
            f"I have been following {comp_name}'s work and appreciate the engineering excellence and product focus. My technical background in {', '.join(skills[:3]) if skills else 'AI and software'} aligns well with the team's mission.",
        f"What relevant experience do you bring to the {job_title} role?":
            f"I have hands-on experience building and deploying end-to-end applications using {', '.join(skills[:4]) if skills else 'Python and related tools'}. I focus on clean design, performance, and reliable delivery.",
        "What is your current notice period and availability?":
            "Available immediately (within 1-2 weeks).",
        "Are you open to hybrid/relocation to the job location if needed?":
            "Yes, I am flexible and excited to collaborate with the team."
    }
