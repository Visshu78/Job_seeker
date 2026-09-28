"""
Domain Resolver — maps company names to their official website domains.
Uses multiple strategies: direct website field, DuckDuckGo, and Clearbit.
"""
import re
import requests
from urllib.parse import urlparse
from utils.logger import get_logger
from utils.rate_limiter import rate_limiter

logger = get_logger("domain-resolver")


class DomainResolver:
    """Resolves a company name or partial URL to a clean domain (e.g. 'stripe.com')."""

    CLEARBIT_URL = "https://autocomplete.clearbit.com/v1/companies/suggest"

    def __init__(self):
        self._cache: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def resolve(self, company_name: str, provided_domain: str = "") -> str:
        """
        Return the best-guess domain for a company.
        Priority: provided_domain > cache > clearbit > duckduckgo
        """
        key = company_name.lower().strip()

        # If the user already provided a domain/URL, clean and return it
        if provided_domain:
            domain = self._clean_domain(provided_domain)
            self._cache[key] = domain
            return domain

        # Check cache
        if key in self._cache:
            return self._cache[key]

        # Try Clearbit autocomplete (free, no API key)
        domain = self._resolve_via_clearbit(company_name)
        if domain:
            self._cache[key] = domain
            logger.info(f"[green]✓[/green] {company_name} → {domain} (Clearbit)")
            return domain

        # Fallback: DuckDuckGo search
        from scrapers.duckduckgo import DuckDuckGoSearch
        ddg = DuckDuckGoSearch()
        domain = ddg.find_company_domain(company_name)
        if domain:
            self._cache[key] = domain
            logger.info(f"[green]✓[/green] {company_name} → {domain} (DuckDuckGo)")
            return domain

        logger.warning(f"[yellow]⚠[/yellow] Could not resolve domain for: {company_name}")
        return ""

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _resolve_via_clearbit(self, company_name: str) -> str:
        """Use Clearbit's free autocomplete API to find the domain."""
        try:
            rate_limiter.wait("free_tools")
            resp = requests.get(
                self.CLEARBIT_URL,
                params={"query": company_name},
                timeout=10,
                headers={"User-Agent": "hr-email-finder/1.0"},
            )
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    return self._clean_domain(data[0].get("domain", ""))
        except Exception as e:
            logger.debug(f"Clearbit lookup failed for {company_name}: {e}")
        return ""

    @staticmethod
    def _clean_domain(url_or_domain: str) -> str:
        """Strip protocol, www, and trailing slashes from a URL or domain."""
        s = url_or_domain.strip().lower()
        if not s:
            return ""
        if "://" not in s:
            s = "https://" + s
        parsed = urlparse(s)
        domain = parsed.netloc or parsed.path
        domain = re.sub(r"^www\.", "", domain)
        domain = domain.split("/")[0]
        return domain
