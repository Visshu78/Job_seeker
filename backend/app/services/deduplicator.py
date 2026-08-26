import re
import hashlib
from typing import List, Tuple, Optional
from difflib import SequenceMatcher

def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return " ".join(text.split())

def canonical_title_keywords(title: str) -> str:
    norm = normalize_text(title)
    norm = norm.replace("ml", "machine learning").replace("sr", "senior").replace("jr", "junior")
    # Strip common filler variations
    tokens = [t for t in norm.split() if t not in ["engineer", "engineering", "developer", "specialist", "the", "and", "in", "for"]]
    return " ".join(sorted(tokens))

def generate_dedup_fingerprint(company: str, title: str, location: str) -> str:
    """Generate canonical fingerprint based on company, core title keywords, and city."""
    norm_comp = normalize_text(company).replace("ai", "").replace("labs", "").replace("technologies", "").strip()
    norm_title = canonical_title_keywords(title)
    
    # Normalize city
    norm_loc = normalize_text(location)
    for city in ["bangalore", "bengaluru", "hyderabad", "pune", "mumbai", "delhi", "gurgaon", "remote"]:
        if city in norm_loc:
            norm_loc = "bangalore" if city == "bengaluru" else city
            break
            
    raw = f"{norm_comp}|{norm_title}|{norm_loc}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def is_duplicate(
    job_a_title: str, job_a_comp: str, job_a_desc: str,
    job_b_title: str, job_b_comp: str, job_b_desc: str,
    threshold: float = 0.70
) -> bool:
    """Check if two job postings are duplicate using title/company similarity and description overlap."""
    norm_c1 = normalize_text(job_a_comp)
    norm_c2 = normalize_text(job_b_comp)
    
    # Must be same or very close company name
    if norm_c1 not in norm_c2 and norm_c2 not in norm_c1:
        c_sim = SequenceMatcher(None, norm_c1, norm_c2).ratio()
        if c_sim < 0.75:
            return False
            
    # Title similarity
    t_sim = SequenceMatcher(None, canonical_title_keywords(job_a_title), canonical_title_keywords(job_b_title)).ratio()
    if t_sim > 0.8:
        return True
        
    # Text token Jaccard similarity for descriptions
    words_a = set(normalize_text(job_a_desc[:600]).split())
    words_b = set(normalize_text(job_b_desc[:600]).split())
    if not words_a or not words_b:
        return t_sim >= 0.75
        
    jaccard = len(words_a & words_b) / float(len(words_a | words_b))
    return (t_sim * 0.6 + jaccard * 0.4) >= threshold
