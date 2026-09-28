"""
RocketReach Enricher
Free tier: 5 lookups/month — https://rocketreach.co/developer
Docs: https://rocketreach.co/api/docs
"""
import requests
from enrichers.base import BaseEnricher, Contact
from utils.logger import get_logger
from utils.rate_limiter import rate_limiter

logger = get_logger("rocketreach")

BASE_URL = "https://api.rocketreach.co/api/v2"


class RocketReachEnricher(BaseEnricher):
    tool_name = "rocketreach"

    def find_people(
        self,
        company: str,
        domain: str,
        roles: list[str],
        max_results: int = 5,
    ) -> list[Contact]:
        if not self.api_key:
            logger.warning("[yellow]RocketReach: no API key set[/yellow]")
            return []
        if not self.is_available():
            logger.warning("[yellow]RocketReach: monthly limit reached[/yellow]")
            return []

        rate_limiter.wait("rocketreach")
        self._increment()

        try:
            resp = requests.post(
                f"{BASE_URL}/search",
                headers={
                    "Api-Key": self.api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "query": {
                        "current_employer": [company],
                        "title": roles,
                    },
                    "start": 1,
                    "pageSize": max_results,
                },
                timeout=20,
            )
            if resp.status_code != 200:
                logger.error(f"RocketReach {resp.status_code}: {resp.text[:200]}")
                return []

            data = resp.json()
            contacts = []
            for p in data.get("profiles", []):
                email = ""
                if p.get("emails"):
                    email = p["emails"][0]

                c = Contact(
                    first_name=p.get("first_name", ""),
                    last_name=p.get("last_name", ""),
                    full_name=p.get("name", ""),
                    title=p.get("current_title", ""),
                    company=company,
                    domain=domain,
                    email=email,
                    email_verified=bool(email),
                    linkedin_url=p.get("linkedin_url", ""),
                    phone=p.get("phones", [""])[0] if p.get("phones") else "",
                    source="rocketreach",
                    confidence=0.8 if email else 0.5,
                    raw=p,
                )
                contacts.append(c)

            logger.info(f"[blue]RocketReach[/blue] found {len(contacts)} contacts at {company}")
            return contacts

        except Exception as ex:
            logger.error(f"RocketReach exception: {ex}")
            return []

    def enrich_email(self, contact: Contact) -> Contact:
        """Lookup a person by LinkedIn URL to retrieve email."""
        if not self.api_key or not contact.linkedin_url:
            return contact
        if not self.is_available():
            return contact

        rate_limiter.wait("rocketreach")
        self._increment()

        try:
            resp = requests.get(
                f"{BASE_URL}/person/lookup",
                headers={"Api-Key": self.api_key},
                params={"linkedin_url": contact.linkedin_url},
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("emails"):
                    contact.email = data["emails"][0]
                    contact.confidence = 0.85
                    contact.source = "rocketreach"
        except Exception as ex:
            logger.debug(f"RocketReach enrich error: {ex}")

        return contact
