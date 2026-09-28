"""
SignalHire Enricher
Free tier: 5 contacts/day — https://www.signalhire.com/api
Docs: https://www.signalhire.com/api/documentation
"""
import requests
from enrichers.base import BaseEnricher, Contact
from utils.logger import get_logger
from utils.rate_limiter import rate_limiter

logger = get_logger("signalhire")

BASE_URL = "https://www.signalhire.com/api/v1"


class SignalHireEnricher(BaseEnricher):
    tool_name = "signalhire"

    def find_people(
        self,
        company: str,
        domain: str,
        roles: list[str],
        max_results: int = 5,
    ) -> list[Contact]:
        """
        Search SignalHire for people at a company by role.
        Note: SignalHire is primarily profile-lookup based.
        Uses search endpoint to find candidates first.
        """
        if not self.api_key:
            logger.warning("[yellow]SignalHire: no API key set[/yellow]")
            return []
        if not self.is_available():
            logger.warning("[yellow]SignalHire: daily limit reached[/yellow]")
            return []

        contacts = []
        for role in roles[:2]:  # conserve free credits
            rate_limiter.wait("signalhire")
            self._increment()

            try:
                resp = requests.post(
                    f"{BASE_URL}/search",
                    headers={
                        "apikey": self.api_key,
                        "Content-Type": "application/json",
                    },
                    json={
                        "current_company": company,
                        "title": role,
                        "count": max_results,
                    },
                    timeout=20,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("items", []):
                        c = self._parse_contact(item, company, domain)
                        contacts.append(c)
                        if len(contacts) >= max_results:
                            break
                else:
                    logger.warning(f"SignalHire {resp.status_code}: {resp.text[:200]}")
            except Exception as ex:
                logger.error(f"SignalHire search error: {ex}")

            if len(contacts) >= max_results:
                break

        logger.info(f"[blue]SignalHire[/blue] found {len(contacts)} contacts at {company}")
        return contacts

    def enrich_email(self, contact: Contact) -> Contact:
        """Lookup a LinkedIn profile URL to retrieve email via SignalHire."""
        if not self.api_key or not contact.linkedin_url:
            return contact
        if not self.is_available():
            return contact

        rate_limiter.wait("signalhire")
        self._increment()

        try:
            resp = requests.post(
                f"{BASE_URL}/candidate/findByItems",
                headers={"apikey": self.api_key, "Content-Type": "application/json"},
                json={"items": [contact.linkedin_url]},
                timeout=20,
            )
            if resp.status_code == 200:
                data = resp.json()
                # SignalHire may return async — check status
                request_id = data.get("requestId")
                if request_id:
                    contact = self._poll_result(request_id, contact)
        except Exception as ex:
            logger.debug(f"SignalHire enrich error: {ex}")

        return contact

    def _poll_result(self, request_id: str, contact: Contact) -> Contact:
        """Poll SignalHire for async result."""
        import time
        for _ in range(5):
            time.sleep(2)
            try:
                resp = requests.get(
                    f"{BASE_URL}/candidate/{request_id}",
                    headers={"apikey": self.api_key},
                    timeout=10,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("items", []):
                        for c in item.get("contacts", []):
                            if c.get("type") == "email":
                                val = c["value"]
                                if any(val.lower().endswith(f"@{d}") for d in ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com"]):
                                    contact.personal_email = val
                                else:
                                    contact.work_email = val
                                contact.email = val
                                contact.email_verified = True
                                contact.source = "signalhire"
                                contact.confidence = 0.85
                                return contact
            except Exception:
                pass
        return contact

    @staticmethod
    def _parse_contact(item: dict, company: str, domain: str) -> Contact:
        name_parts = (item.get("name") or "").split(" ", 1)
        return Contact(
            first_name=name_parts[0] if name_parts else "",
            last_name=name_parts[1] if len(name_parts) > 1 else "",
            full_name=item.get("name", ""),
            title=item.get("title", ""),
            company=company,
            domain=domain,
            linkedin_url=item.get("linkedin", ""),
            source="signalhire",
            confidence=0.7,
            raw=item,
        )
