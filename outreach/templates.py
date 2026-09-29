"""
Template Manager for Recruiter Outreach.
Supports dynamic user-defined custom links (Portfolio, LinkedIn, GitHub, etc.)
with dynamic variables and intelligent fallback values.
"""
import re
from typing import Dict, Any, List

DEFAULT_TEMPLATES = [
    {
        "id": "recruiter_application",
        "name": "Job Application to Recruiter / TA Lead",
        "subject": "Application: {{Role}} role at {{Company}} — {{My_Name}}",
        "body": """Hi {{First_Name}},

I hope your week is off to a great start!

I noticed you lead recruiting and talent acquisition at {{Company}}. I'm reaching out because I am very interested in {{Role}} opportunities on your team.

A quick summary of what I bring:
• Extensive experience in software development, modern architectures, and product engineering.
• Proven background delivering scalable features and collaborating across cross-functional teams.

I have attached my resume for your review. You can also explore my work and profiles here:
{{All_Links}}

Would you have 5-10 minutes for a brief introductory call, or could you point me to the hiring manager for this role?

Thank you for your time and consideration!

Best regards,
{{My_Name}}
{{My_Phone}}
{{My_Email}}"""
    },
    {
        "id": "hiring_manager_inquiry",
        "name": "Direct Outreach to Engineering / Department Lead",
        "subject": "Quick inquiry regarding {{Role}} opportunities at {{Company}}",
        "body": """Hi {{First_Name}},

I came across your profile while following the impressive work {{Company}} is doing.

Given your leadership as {{Title}}, I wanted to reach out directly to express my strong interest in joining your team as a {{Role}}.

Key highlights of my background:
• Strong track record in building high-quality, resilient systems.
• Passionate about solving complex product problems and moving fast.

I've attached my resume and would welcome the opportunity to connect for a quick 10-minute chat to discuss how I could contribute to {{Company}}'s goals.

My profiles & links:
{{All_Links}}

Best regards,
{{My_Name}}
{{My_Email}}
{{My_Phone}}"""
    },
    {
        "id": "follow_up",
        "name": "Polite Follow-up (1 Week Later)",
        "subject": "Re: Application: {{Role}} role at {{Company}} — {{My_Name}}",
        "body": """Hi {{First_Name}},

I hope you're having a productive week!

I wanted to quickly follow up on my note from last week regarding the {{Role}} opportunity at {{Company}}.

I remain very excited about the mission and would love to speak if you are still reviewing candidates. My resume is attached for quick reference.

Thanks again for your time,
{{My_Name}}
{{LinkedIn_URL}}"""
    }
]


def extract_first_name(full_name: str) -> str:
    """Extract a friendly first name from a full name string."""
    if not full_name:
        return "there"
    clean = re.sub(r'^(mr\.|ms\.|mrs\.|dr\.)\s+', '', full_name.strip(), flags=re.IGNORECASE)
    parts = clean.split()
    return parts[0].capitalize() if parts else "there"


def build_all_links_block(profile: Dict[str, Any]) -> str:
    """Construct a clean, bulleted list of all non-empty links provided in the candidate profile."""
    links = []
    custom_links = profile.get("custom_links") or []

    if isinstance(custom_links, list):
        for item in custom_links:
            if isinstance(item, dict) and item.get("url"):
                label = (item.get("label") or "Link").strip()
                url = item.get("url", "").strip()
                if url:
                    links.append(f"• {label}: {url}")

    # Fallback to legacy single fields if custom_links was empty
    if not links:
        if profile.get("portfolio_url"):
            links.append(f"• Portfolio: {profile['portfolio_url'].strip()}")
        if profile.get("linkedin_url"):
            links.append(f"• LinkedIn: {profile['linkedin_url'].strip()}")
        if profile.get("github_url"):
            links.append(f"• GitHub: {profile['github_url'].strip()}")
        if profile.get("calendly_url"):
            links.append(f"• Schedule a chat: {profile['calendly_url'].strip()}")
        if profile.get("other_url"):
            label = profile.get("other_url_label", "Website").strip() or "Website"
            links.append(f"• {label}: {profile['other_url'].strip()}")

    return "\n".join(links) if links else ""


def render_template(
    template_str: str,
    contact: Dict[str, Any],
    profile: Dict[str, Any]
) -> str:
    """
    Render template string replacing {{Variable}} placeholders.
    """
    full_name = contact.get("Name") or contact.get("First Name", "")
    first_name = contact.get("First Name") or extract_first_name(full_name)
    company = contact.get("Company", "your team")
    title = contact.get("Title", "Recruiter")
    role = profile.get("target_role", "Software Engineer")
    my_name = profile.get("my_name", "")
    my_email = profile.get("my_email", "")
    my_phone = profile.get("my_phone", "")

    all_links = build_all_links_block(profile)

    recruiter_email = contact.get("Work Email") or contact.get("Primary Email") or contact.get("email") or ""
    recruiter_linkedin = contact.get("LinkedIn") or contact.get("linkedin_url") or ""
    clean_co = re.sub(r'[^A-Za-z0-9]', '', company).upper()[:8] or "JOB"
    ref_id = f"REF-{clean_co}-{abs(hash(full_name or company)) % 10000:04d}"

    mapping = {
        "{{Recruiter_Name}}": full_name or "Hiring Team",
        "{{recruiter_name}}": full_name or "Hiring Team",
        "{{Recruiter_Title}}": title or "Talent Acquisition / HR",
        "{{recruiter_title}}": title or "Talent Acquisition / HR",
        "{{Recruiter_Email}}": recruiter_email,
        "{{recruiter_email}}": recruiter_email,
        "{{Recruiter_LinkedIn}}": recruiter_linkedin,
        "{{recruiter_linkedin}}": recruiter_linkedin,
        "{{Tracking_Ref}}": ref_id,
        "{{tracking_ref}}": ref_id,
        "{{Reference_ID}}": ref_id,
        "{{reference_id}}": ref_id,
        "{{First_Name}}": first_name or "there",
        "{{first_name}}": first_name or "there",
        "{{Name}}": full_name or "there",
        "{{name}}": full_name or "there",
        "{{Company}}": company or "your company",
        "{{company}}": company or "your company",
        "{{Title}}": title or "Hiring Team",
        "{{title}}": title or "Hiring Team",
        "{{Role}}": role,
        "{{role}}": role,
        "{{My_Name}}": my_name,
        "{{my_name}}": my_name,
        "{{My_Email}}": my_email,
        "{{my_email}}": my_email,
        "{{My_Phone}}": my_phone,
        "{{my_phone}}": my_phone,
        "{{All_Links}}": all_links,
        "{{all_links}}": all_links,
        # Default fallbacks
        "{{Portfolio_URL}}": profile.get("portfolio_url", ""),
        "{{portfolio_url}}": profile.get("portfolio_url", ""),
        "{{LinkedIn_URL}}": profile.get("linkedin_url", ""),
        "{{linkedin_url}}": profile.get("linkedin_url", ""),
        "{{GitHub_URL}}": profile.get("github_url", ""),
        "{{github_url}}": profile.get("github_url", ""),
        "{{Calendly_URL}}": profile.get("calendly_url", ""),
        "{{calendly_url}}": profile.get("calendly_url", ""),
        "{{Other_URL}}": profile.get("other_url", ""),
        "{{other_url}}": profile.get("other_url", ""),
    }

    # Map all custom links dynamically by label
    custom_links = profile.get("custom_links") or []
    if isinstance(custom_links, list):
        for item in custom_links:
            if isinstance(item, dict) and item.get("label"):
                lbl = item.get("label", "").strip()
                url = item.get("url", "").strip()
                safe_key = re.sub(r'[^A-Za-z0-9_]', '', lbl.replace(' ', '_'))
                if safe_key:
                    mapping['{{' + safe_key + '_URL}}'] = url
                    mapping['{{' + safe_key + '_url}}'] = url
                    mapping['{{' + safe_key + '}}'] = url
                    mapping['{{' + lbl + '}}'] = url

                # Also match common canonical names
                lbl_lower = lbl.lower()
                if "linkedin" in lbl_lower:
                    mapping["{{LinkedIn_URL}}"] = url
                    mapping["{{linkedin_url}}"] = url
                elif "github" in lbl_lower:
                    mapping["{{GitHub_URL}}"] = url
                    mapping["{{github_url}}"] = url
                elif "portfolio" in lbl_lower or "website" in lbl_lower:
                    mapping["{{Portfolio_URL}}"] = url
                    mapping["{{portfolio_url}}"] = url
                elif "calendly" in lbl_lower or "meeting" in lbl_lower or "chat" in lbl_lower:
                    mapping["{{Calendly_URL}}"] = url
                    mapping["{{calendly_url}}"] = url

    result = template_str
    for tag, val in mapping.items():
        result = result.replace(tag, str(val))

    # Clean up any lines that ended up as empty bullets
    lines = result.split("\n")
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if re.match(r'^[•\-\*]\s+[A-Za-z0-9_\s]+:\s*$', stripped):
            continue
        cleaned_lines.append(line)

    result = "\n".join(cleaned_lines)
    result = re.sub(r'\{\{[A-Za-z0-9_]+\}\}', '', result)
    return result
