"""
Apollo.io Enricher
Free tier: 50 email exports/month — https://app.apollo.io/settings/integrations/api
Docs: https://apolloio.github.io/apollo-api-docs/
"""
import requests
from enrichers.base import BaseEnricher, Contact
from utils.logger import get_logger
from utils.rate_limiter import rate_limiter

logger = get_logger("apollo-io")

BASE_URL = "https://api.apollo.io/v1"


class ApolloIOEnricher(BaseEnricher):
    tool_name = "apollo_io"

    def find_people(
        self,
        company: str,
        domain: str,
        roles: list[str],
        max_results: int = 5,
    ) -> list[Contact]:
        """Search Apollo for people by company domain and title keywords."""
        if not self.api_key:
            logger.warning("[yellow]Apollo.io: no API key set[/yellow]")
            return []
        if not self.is_available():
            logger.warning("[yellow]Apollo.io: daily limit reached[/yellow]")
            return []

        rate_limiter.wait("apollo_io")
        self._increment()

        try:
            resp = requests.post(
                f"{BASE_URL}/mixed_people/search",
                headers={
                    "Content-Type": "application/json",
                    "Cache-Control": "no-cache",
                    "X-Api-Key": self.api_key,
                },
                json={
                    "organization_domains": [domain],
                    "person_titles": roles,
                    "page": 1,
                    "per_page": max_results,
                },
                timeout=20,
            )
            if resp.status_code != 200:
                logger.error(f"Apollo.io error {resp.status_code}: {resp.text[:300]}")
                return []

            data = resp.json()
            people = data.get("people", [])
            contacts = []

            for p in people:
                email = p.get("email", "")
                if not email:
                    email = self._enrich_person_email(p.get("id", ""))

                personal_emails = p.get("personal_emails", []) or []
                personal_email = personal_emails[0] if personal_emails else ""
                work_email = ""
                if email:
                    if any(email.lower().endswith(f"@{d}") for d in ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"]):
                        if not personal_email:
                            personal_email = email
                    else:
                        work_email = email

                org = p.get("organization", {}) or {}
                c = Contact(
                    first_name=p.get("first_name", ""),
                    last_name=p.get("last_name", ""),
                    full_name=p.get("name", ""),
                    title=p.get("title", ""),
                    company=org.get("name", company),
                    domain=domain,
                    email=work_email or personal_email or email,
                    work_email=work_email,
                    personal_email=personal_email,
                    email_verified=bool(email),
                    linkedin_url=p.get("linkedin_url", ""),
                    phone=self._extract_phone(p),
                    source="apollo_io",
                    confidence=0.85 if (work_email or personal_email or email) else 0.5,
                    raw=p,
                )
                contacts.append(c)

            logger.info(f"[blue]Apollo.io[/blue] found {len(contacts)} contacts at {domain}")
            return contacts

        except Exception as ex:
            logger.error(f"Apollo.io exception: {ex}")
            return []

    def enrich_email(self, contact: Contact) -> Contact:
        """Use Apollo's people/match endpoint to find an email for a contact."""
        if not self.api_key:
            return contact
        if not self.is_available():
            return contact

        rate_limiter.wait("apollo_io")
        self._increment()

        try:
            resp = requests.post(
                f"{BASE_URL}/people/match",
                headers={
                    "Content-Type": "application/json",
                    "X-Api-Key": self.api_key,
                },
                json={
                    "first_name": contact.first_name,
                    "last_name": contact.last_name,
                    "organization_name": contact.company,
                    "domain": contact.domain,
                    "reveal_personal_emails": False,
                },
                timeout=20,
            )
            if resp.status_code == 200:
                data = resp.json()
                person = data.get("person", {})
                email = person.get("email", "")
                if email:
                    contact.email = email
                    contact.confidence = 0.85
                    contact.source = "apollo_io"
        except Exception as ex:
            logger.debug(f"Apollo.io enrich error: {ex}")

        return contact

    def _enrich_person_email(self, person_id: str) -> str:
        """Request email reveal for a specific person ID (uses credits)."""
        if not person_id:
            return ""
        try:
            resp = requests.post(
                f"{BASE_URL}/people/bulk_match",
                headers={"Content-Type": "application/json", "X-Api-Key": self.api_key},
                json={"details": [{"id": person_id}]},
                timeout=15,
            )
            if resp.status_code == 200:
                matches = resp.json().get("matches", [])
                if matches:
                    return matches[0].get("email", "")
        except Exception:
            pass
        return ""

    @staticmethod
    def _extract_phone(person: dict) -> str:
        phones = person.get("phone_numbers", [])
        if phones:
            return phones[0].get("sanitized_number", "")
        return ""
