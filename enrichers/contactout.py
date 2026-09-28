"""
ContactOut Enricher
Free tier: 40 exports/month — https://contactout.com
Docs: https://api.contactout.com/
"""
import requests
from enrichers.base import BaseEnricher, Contact
from utils.logger import get_logger
from utils.rate_limiter import rate_limiter

logger = get_logger("contactout")

BASE_URL = "https://api.contactout.com/v1"


class ContactOutEnricher(BaseEnricher):
    tool_name = "contactout"

    def find_people(
        self,
        company: str,
        domain: str,
        roles: list[str],
        max_results: int = 5,
    ) -> list[Contact]:
        if not self.api_key:
            logger.warning("[yellow]ContactOut: no API key set[/yellow]")
            return []
        if not self.is_available():
            logger.warning("[yellow]ContactOut: monthly limit reached[/yellow]")
            return []

        rate_limiter.wait("contactout")
        self._increment()

        try:
            resp = requests.get(
                f"{BASE_URL}/people/search",
                headers={"Authorization": f"basic {self.api_key}"},
                params={
                    "company_domain": domain,
                    "title": roles[0] if roles else "HR",
                    "limit": max_results,
                },
                timeout=20,
            )
            if resp.status_code != 200:
                logger.error(f"ContactOut {resp.status_code}: {resp.text[:200]}")
                return []

            data = resp.json()
            contacts = []
            for p in data.get("data", []):
                c = Contact(
                    full_name=p.get("name", ""),
                    title=p.get("title", ""),
                    company=company,
                    domain=domain,
                    email=p.get("email", ""),
                    email_verified=bool(p.get("email")),
                    linkedin_url=p.get("linkedin", ""),
                    source="contactout",
                    confidence=0.8,
                    raw=p,
                )
                contacts.append(c)

            logger.info(f"[blue]ContactOut[/blue] found {len(contacts)} contacts at {company}")
            return contacts

        except Exception as ex:
            logger.error(f"ContactOut exception: {ex}")
            return []

    def enrich_email(self, contact: Contact) -> Contact:
        """Lookup via LinkedIn URL."""
        if not self.api_key or not contact.linkedin_url:
            return contact
        if not self.is_available():
            return contact

        rate_limiter.wait("contactout")
        self._increment()

        try:
            resp = requests.get(
                f"{BASE_URL}/people/email",
                headers={"Authorization": f"basic {self.api_key}"},
                params={"linkedin_url": contact.linkedin_url},
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                email = data.get("email", "")
                if email:
                    contact.email = email
                    contact.confidence = 0.85
                    contact.source = "contactout"
        except Exception as ex:
            logger.debug(f"ContactOut enrich error: {ex}")

        return contact
