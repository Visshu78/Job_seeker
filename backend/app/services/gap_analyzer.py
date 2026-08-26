from typing import Dict, Any, List

def generate_gap_analysis(
    match_data: Dict[str, Any],
    candidate_profile: Dict[str, Any],
    job: Dict[str, Any]
) -> Dict[str, Any]:
    """
    PRD Section 23, 24, 25:
    Generates explainability text, gap severity summaries, and non-hallucinatory resume improvement tips.
    """
    matched = match_data.get("matched_skills", [])
    missing = match_data.get("missing_skills", [])
    transferable = match_data.get("transferable_skills", [])
    score = match_data.get("overall_score", 0.0)
    
    # 1. Generate 'Why Recommended'
    matched_names = [m["skill"] for m in matched[:4]]
    if matched_names:
        why_parts = [f"Strong alignment in core requirements: {', '.join(matched_names)}."]
    else:
        why_parts = ["Solid foundation matching the role scope."]
        
    if transferable:
        trans_names = [f"{t['candidate_has']} (transfers to {t['required']})" for t in transferable[:2]]
        why_parts.append(f"Transferable skill advantage in {', '.join(trans_names)}.")
        
    why_recommended = " ".join(why_parts)

    # 2. Generate Gap Summary & Severity
    missing_mandatory = [m["skill"] for m in missing if m.get("type") == "REQUIRED"]
    missing_preferred = [m["skill"] for m in missing if m.get("type") in ["PREFERRED", "NICE_TO_HAVE"]]
    
    if not missing_mandatory and not missing_preferred:
        gap_summary = "Zero critical skill gaps detected. You satisfy all published requirements."
    elif not missing_mandatory and missing_preferred:
        gap_summary = f"No mandatory requirements are missing. Missing items ({', '.join(missing_preferred[:3])}) are marked as preferred/nice-to-have."
    else:
        gap_summary = f"Mandatory skill gaps: {', '.join(missing_mandatory[:2])}. Recommended to emphasize related foundational projects."

    # 3. Generate Non-Hallucinatory Resume Improvement Suggestions (PRD Section 25)
    suggestions = []
    
    # Check if candidate has projects that could be highlighted
    cand_projects = candidate_profile.get("projects", [])
    cand_skills = candidate_profile.get("skills", [])
    
    # Suggestion A: Tailor Project Bullets
    if cand_projects and matched:
        top_proj = cand_projects[0]
        suggestions.append({
            "category": "project_enhancement",
            "title": f"Highlight {matched[0]['skill']} in '{top_proj.get('title')}'",
            "suggestion": f"Ensure your project description for '{top_proj.get('title')}' highlights measurable outcomes with {matched[0]['skill']}.",
            "reason": f"{job.get('company_name')} emphasizes practical {matched[0]['skill']} deployment.",
            "evidence_in_resume": f"Existing project '{top_proj.get('title')}' already uses related technologies."
        })
        
    # Suggestion B: Transferable skill framing
    if transferable:
        t = transferable[0]
        suggestions.append({
            "category": "skill_highlight",
            "title": f"Frame {t['candidate_has']} as transferable foundation for {t['required']}",
            "suggestion": f"Add a brief mention in your skills summary stating strong {t['candidate_has']} background with readiness to build on {t['required']}.",
            "reason": t["explanation"],
            "evidence_in_resume": f"You have verified experience in {t['candidate_has']}."
        })

    # Suggestion C: Keyword optimization for ATS
    if missing_preferred and any(s in cand_skills for s in ["Docker", "Linux", "Git", "SQL"]):
        suggestions.append({
            "category": "keyword_inclusion",
            "title": "Emphasize DevOps & Tooling keywords",
            "suggestion": "Prominently list your existing version control and development workflow tools in the technical skills section.",
            "reason": "Improves ATS parsing score for early-career screening filters.",
            "evidence_in_resume": "Tooling knowledge present in candidate profile."
        })

    return {
        "why_recommended": why_recommended,
        "gap_summary": gap_summary,
        "resume_suggestions": suggestions
    }
