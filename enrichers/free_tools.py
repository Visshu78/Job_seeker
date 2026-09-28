"""
Free Tools Enricher - zero-cost email discovery using:
 1. DDGS (DuckDuckGo Search) library for LinkedIn profile discovery
 2. Email pattern generation + SMTP verification
 3. Bing people search as fallback
No API keys required.
"""
import re
import requests
from bs4 import BeautifulSoup
import urllib.parse
import time

from enrichers.base import BaseEnricher, Contact
from email_utils.patterns import EmailPatternGenerator
from email_utils.smtp_verifier import SMTPVerifier
from utils.logger import get_logger
from utils.rate_limiter import rate_limiter

logger = get_logger("free-tools")

PERSONAL_DOMAINS = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
                    "icloud.com", "protonmail.com", "aol.com", "live.com"}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

# Queries that reliably return LinkedIn /in/ profiles
DDGS_QUERY_PATTERNS = [
    '"{role}" "{company}" site:linkedin.com/in',
    '{company} {role} linkedin',
    '"{company}" "{role}" linkedin profile',
]


class FreeToolsEnricher(BaseEnricher):
    tool_name = "free_tools"

    def __init__(self, config: dict):
        super().__init__(config)
        self.use_smtp = config.get("use_smtp_verify", True)
        self.use_patterns = config.get("use_pattern_guess", True)
        self.use_ddg = config.get("use_duckduckgo", True)
        self.use_linkedin = config.get("use_linkedin_scrape", False)
        self._pattern_gen = EmailPatternGenerator()
        self._smtp = SMTPVerifier()

    def find_people(
        self,
        company: str,
        domain: str,
        roles: list[str],
        max_results: int = 5,
    ) -> list[Contact]:
        """Find real people via DDGS LinkedIn search."""
        contacts = []

        # Strategy 1: DDGS (primary — works very well)
        if self.use_ddg:
            contacts.extend(
                self._ddgs_search(company, domain, roles, max_results)
            )

        # Strategy 2: LinkedIn Playwright scraper (requires li_at cookie)
        if self.use_linkedin and len(contacts) < max_results:
            from scrapers.linkedin_scraper import LinkedInScraper
            li_at = self.config.get("li_at_cookie", "")
            scraper = LinkedInScraper(li_at_cookie=li_at)
            li_people = scraper.find_people(company, roles, max_results - len(contacts))
            for p in li_people:
                name = p.get("name", "")
                parts = name.split(" ", 1)
                c = Contact(
                    first_name=parts[0] if parts else "",
                    last_name=parts[1] if len(parts) > 1 else "",
                    full_name=name,
                    title=p.get("title", ""),
                    company=company,
                    domain=domain,
                    linkedin_url=p.get("profile_url", ""),
                    source="linkedin",
                    confidence=0.6,
                )
                contacts.append(c)

        # De-duplicate by LinkedIn URL or name
        seen_urls = set()
        seen_names = set()
        unique = []
        for c in contacts:
            url_key = c.linkedin_url.rstrip("/")
            name_key = c.name.lower().strip()
            if url_key and url_key in seen_urls:
                continue
            if not url_key and name_key in seen_names:
                continue
            seen_urls.add(url_key)
            seen_names.add(name_key)
            unique.append(c)

        logger.info(f"[blue]Free Tools[/blue] found {len(unique)} candidates at {company}")
        return unique[:max_results]

    # ------------------------------------------------------------------
    # DDGS Search
    # ------------------------------------------------------------------

    def _ddgs_search(self, company: str, domain: str, roles: list[str], max_results: int) -> list[Contact]:
        """Use DDGS to find real LinkedIn profiles for people at a company."""
        contacts = []
        try:
            from ddgs import DDGS
        except ImportError:
            try:
                from duckduckgo_search import DDGS
            except ImportError:
                logger.warning("[yellow]Install ddgs: pip install ddgs[/yellow]")
                return contacts

        role_queries = [
            (roles[0] if roles else "Recruiter",
             f'"{roles[0] if roles else "Recruiter"}" "{company}" site:linkedin.com/in'),
            ("HR",
             f'{company} HR Manager linkedin'),
            (roles[1] if len(roles) > 1 else "",
             f'{company} Recruiter linkedin profile' if len(roles) <= 1 else
             f'"{roles[1]}" "{company}" site:linkedin.com/in'),
        ]

        for role_hint, query in role_queries:
            if len(contacts) >= max_results:
                break
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=8))

                for r in results:
                    href = r.get("href", "")
                    title_raw = r.get("title", "")
                    body = r.get("body", "")

                    if not href or "linkedin.com/in/" not in href:
                        continue

                    # Each result title may contain multiple concatenated profiles
                    # Extract just the first profile
                    first_title = self._extract_first_profile_title(title_raw)
                    name, detected_title = self._parse_linkedin_title(first_title or title_raw)

                    if not name:
                        name, detected_title = self._extract_name_from_url(href)

                    if not name:
                        continue

                    parts = name.split(" ", 1)
                    c = Contact(
                        first_name=parts[0],
                        last_name=parts[1] if len(parts) > 1 else "",
                        full_name=name,
                        title=detected_title or role_hint,
                        company=company,
                        domain=domain,
                        linkedin_url=href,
                        source="ddgs_linkedin",
                        confidence=0.65,
                        notes=body[:120] if body else "",
                    )
                    contacts.append(c)

                    if len(contacts) >= max_results:
                        break

                time.sleep(1)  # Be polite
            except Exception as e:
                logger.debug(f"DDGS query '{query}' error: {e}")

        return contacts

    # ------------------------------------------------------------------
    # Email Enrichment
    # ------------------------------------------------------------------

    def enrich_email(self, contact: Contact) -> Contact:
        """Generate email candidates using patterns and verify via SMTP."""
        if contact.email and contact.email_verified:
            return contact
        if not contact.domain or not (contact.first_name or contact.full_name):
            return contact

        if not contact.first_name and contact.full_name:
            parts = contact.full_name.strip().split()
            contact.first_name = parts[0]
            contact.last_name = parts[-1] if len(parts) > 1 else ""

        if not self.use_patterns:
            return contact

        candidates = self._pattern_gen.generate(
            first=contact.first_name,
            last=contact.last_name,
            domain=contact.domain,
        )

        logger.info(
            f"[dim]Trying {len(candidates)} email patterns for "
            f"{contact.first_name} {contact.last_name} @{contact.domain}[/dim]"
        )

        for email, pattern_confidence in candidates:
            if self.use_smtp:
                result = self._smtp.verify(email)
                if result["valid"]:
                    contact.email = email
                    contact.work_email = email
                    contact.email_verified = True
                    contact.email_type = result.get("type", "professional")
                    contact.confidence = min(0.9, pattern_confidence + 0.2)
                    contact.source = contact.source + ":smtp"
                    logger.info(
                        f"[green]Verified email: {email} "
                        f"(confidence: {contact.confidence:.0%})[/green]"
                    )
                    return contact
            else:
                contact.email = email
                contact.work_email = email
                contact.email_verified = False
                contact.confidence = pattern_confidence
                contact.source = contact.source + ":pattern"
                return contact

        return contact

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_first_profile_title(title: str) -> str:
        """
        DDGS sometimes returns concatenated results like:
        'Julie Fox - HR Manager at Stripe | LinkedInErica Fox - Recruiter...'
        Extract only the first profile's title.
        """
        # Split on 'LinkedIn' followed by a capital letter (start of next profile)
        parts = re.split(r'LinkedIn(?=[A-Z])', title)
        return parts[0].strip() if parts else title

    @staticmethod
    def _parse_linkedin_title(title: str) -> tuple[str, str]:
        """
        Parse: 'John Doe - HR Manager at Stripe | LinkedIn'
        Returns: ('John Doe', 'HR Manager')
        """
        title = re.sub(r"\s*\|?\s*LinkedIn\s*$", "", title, flags=re.IGNORECASE).strip()
        # Pattern: "Name - Title at Company" or "Name | Title"
        m = re.match(r"^([A-Z][^-|]+?)\s*[-|]\s*(.+?)(?:\s+(?:at|@)\s+.+)?$", title)
        if m:
            name_candidate = m.group(1).strip()
            title_candidate = m.group(2).strip()
            name_words = name_candidate.split()
            # Name: 1-4 words, doesn't look like a job title
            if 1 <= len(name_words) <= 5 and not re.search(
                r'\b(manager|director|recruiter|partner|specialist|lead|engineer|analyst|head|officer|vp|president)\b',
                name_candidate, re.I
            ):
                return name_candidate, title_candidate
        return "", ""

    @staticmethod
    def _extract_name_from_url(url: str) -> tuple[str, str]:
        """
        Derive a guess at the person's name from their LinkedIn slug.
        e.g. linkedin.com/in/john-doe-123 -> 'John Doe'
        """
        m = re.search(r"linkedin\.com/in/([^/?#]+)", url)
        if not m:
            return "", ""
        slug = m.group(1)
        # Remove trailing numbers/IDs
        slug = re.sub(r"-\w{5,}$", "", slug)
        parts = slug.split("-")
        name_parts = [p.capitalize() for p in parts if p.isalpha()]
        if len(name_parts) >= 2:
            return " ".join(name_parts[:3]), ""
        return "", ""
