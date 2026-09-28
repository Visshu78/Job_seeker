"""
Hunter.io Enricher
Free tier: 25 searches/month — https://hunter.io/users/sign_up
Docs: https://hunter.io/api-documentation
"""
import requests
from enrichers.base import BaseEnricher, Contact
from utils.logger import get_logger
from utils.rate_limiter import rate_limiter

logger = get_logger("hunter-io")

BASE_URL = "https://api.hunter.io/v2"


class HunterIOEnricher(BaseEnricher):
    tool_name = "hunter_io"

    def find_people(
        self,
        company: str,
        domain: str,
        roles: list[str],
        max_results: int = 5,
    ) -> list[Contact]:
        """
        Use Hunter's /domain-search to find emails at a domain.
        Filters results by role keywords.
        """
        if not self.api_key:
            logger.warning("[yellow]Hunter.io: no API key set[/yellow]")
            return []
        if not self.is_available():
            logger.warning("[yellow]Hunter.io: monthly limit reached[/yellow]")
            return []

        rate_limiter.wait("hunter_io")
        self._increment()

        try:
            resp = requests.get(
                f"{BASE_URL}/domain-search",
                params={
                    "domain": domain,
                    "api_key": self.api_key,
                    "limit": 20,
                    "type": "personal",
                },
                timeout=15,
            )
            data = resp.json()
            if resp.status_code != 200:
                logger.error(f"Hunter.io error: {data.get('errors', resp.status_code)}")
                return []

            emails = data.get("data", {}).get("emails", [])
            contacts = []
            roles_lower = [r.lower() for r in roles]

            for e in emails:
                title = (e.get("position") or "").lower()
                dept = (e.get("department") or "").lower()

                # Filter by role match
                if not any(kw in title or kw in dept for kw in roles_lower):
                    continue

                c = Contact(
                    first_name=e.get("first_name", ""),
                    last_name=e.get("last_name", ""),
                    title=e.get("position", ""),
                    company=company,
                    domain=domain,
                    email=e.get("value", ""),
                    email_verified=e.get("verification", {}).get("status") == "valid",
                    email_type=e.get("type", ""),
                    linkedin_url=e.get("linkedin", ""),
                    source="hunter_io",
                    confidence=e.get("confidence", 0) / 100.0,
                    raw=e,
                )
                contacts.append(c)
                if len(contacts) >= max_results:
                    break

            logger.info(
                f"[blue]Hunter.io[/blue] found {len(contacts)} contacts at {domain}"
            )
            return contacts

        except Exception as ex:
            logger.error(f"Hunter.io exception: {ex}")
            return []

    def enrich_email(self, contact: Contact) -> Contact:
        """Use Hunter's /email-finder to find a specific person's email."""
        if not self.api_key or not contact.domain:
            return contact
        if not self.is_available():
            return contact

        rate_limiter.wait("hunter_io")
        self._increment()

        try:
            resp = requests.get(
                f"{BASE_URL}/email-finder",
                params={
                    "domain": contact.domain,
                    "first_name": contact.first_name,
                    "last_name": contact.last_name,
                    "api_key": self.api_key,
                },
                timeout=15,
            )
            data = resp.json()
            if resp.status_code == 200:
                result = data.get("data", {})
                email = result.get("email", "")
                if email:
                    contact.email = email
                    contact.confidence = result.get("score", 0) / 100.0
                    contact.source = "hunter_io"
                    contact.email_verified = (
                        result.get("verification", {}).get("status") == "valid"
                    )
        except Exception as ex:
            logger.debug(f"Hunter.io enrich error: {ex}")

        return contact
