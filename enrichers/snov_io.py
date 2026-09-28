"""
Snov.io Enricher
Free tier: 50 credits/month — https://app.snov.io/api-setting
Docs: https://snov.io/api
"""
import requests
from enrichers.base import BaseEnricher, Contact
from utils.logger import get_logger
from utils.rate_limiter import rate_limiter

logger = get_logger("snov-io")

BASE_URL = "https://api.snov.io/v1"
TOKEN_URL = "https://api.snov.io/v1/oauth/access_token"


class SnovIOEnricher(BaseEnricher):
    tool_name = "snov_io"

    def __init__(self, config: dict):
        super().__init__(config)
        self.client_id = config.get("client_id", "")
        self.client_secret = config.get("client_secret", "")
        self._token: str = ""

    def find_people(
        self,
        company: str,
        domain: str,
        roles: list[str],
        max_results: int = 5,
    ) -> list[Contact]:
        """Find emails at a domain using Snov.io's domain-emails endpoint."""
        if not (self.client_id and self.client_secret):
            logger.warning("[yellow]Snov.io: client_id/client_secret not configured[/yellow]")
            return []
        if not self.is_available():
            logger.warning("[yellow]Snov.io: credit limit reached[/yellow]")
            return []

        token = self._get_token()
        if not token:
            return []

        rate_limiter.wait("snov_io")
        self._increment()

        try:
            resp = requests.get(
                f"{BASE_URL}/get-domain-emails-with-info",
                params={
                    "access_token": token,
                    "domain": domain,
                    "type": "personal",
                    "limit": 20,
                },
                timeout=20,
            )
            data = resp.json()
            if not data.get("success"):
                logger.error(f"Snov.io error: {data}")
                return []

            contacts = []
            roles_lower = [r.lower() for r in roles]

            for item in data.get("emails", []):
                position = (item.get("position") or "").lower()
                if not any(kw in position for kw in roles_lower):
                    continue

                name = item.get("name", "")
                parts = name.split(" ", 1)
                c = Contact(
                    first_name=parts[0] if parts else "",
                    last_name=parts[1] if len(parts) > 1 else "",
                    full_name=name,
                    title=item.get("position", ""),
                    company=company,
                    domain=domain,
                    email=item.get("email", ""),
                    email_verified=item.get("emailStatus") == "valid",
                    source="snov_io",
                    confidence=0.75,
                    raw=item,
                )
                contacts.append(c)
                if len(contacts) >= max_results:
                    break

            logger.info(f"[blue]Snov.io[/blue] found {len(contacts)} contacts at {domain}")
            return contacts

        except Exception as ex:
            logger.error(f"Snov.io exception: {ex}")
            return []

    def enrich_email(self, contact: Contact) -> Contact:
        """Use Snov.io's email-by-name endpoint."""
        token = self._get_token()
        if not token or not contact.domain:
            return contact
        if not self.is_available():
            return contact

        rate_limiter.wait("snov_io")
        self._increment()

        try:
            resp = requests.get(
                f"{BASE_URL}/get-emails-by-name",
                params={
                    "access_token": token,
                    "domain": contact.domain,
                    "firstName": contact.first_name,
                    "lastName": contact.last_name,
                },
                timeout=15,
            )
            data = resp.json()
            if data.get("success") and data.get("emails"):
                email = data["emails"][0].get("email", "")
                if email:
                    contact.email = email
                    contact.confidence = 0.75
                    contact.source = "snov_io"
        except Exception as ex:
            logger.debug(f"Snov.io enrich error: {ex}")

        return contact

    def _get_token(self) -> str:
        """Obtain OAuth2 access token."""
        if self._token:
            return self._token
        try:
            resp = requests.post(
                TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                timeout=10,
            )
            if resp.status_code == 200:
                self._token = resp.json().get("access_token", "")
                return self._token
        except Exception as ex:
            logger.error(f"Snov.io token error: {ex}")
        return ""
