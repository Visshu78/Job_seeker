"""
DuckDuckGo Search — free, no-API-key web search for company domains and people.
"""
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, quote_plus
from utils.logger import get_logger
from utils.rate_limiter import rate_limiter

logger = get_logger("duckduckgo")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


class DuckDuckGoSearch:
    """
    Uses DuckDuckGo HTML search (free, no API key) to find
    company domains and surface contact-related pages.
    """

    DDG_URL = "https://html.duckduckgo.com/html/"

    def search(self, query: str, max_results: int = 5) -> list[dict]:
        """
        Perform a DuckDuckGo search and return a list of
        {'title': ..., 'url': ..., 'snippet': ...} dicts.
        """
        rate_limiter.wait("duckduckgo")
        try:
            resp = requests.post(
                self.DDG_URL,
                data={"q": query, "b": ""},
                headers=HEADERS,
                timeout=15,
            )
            if resp.status_code != 200:
                logger.warning(f"DuckDuckGo returned {resp.status_code}")
                return []

            soup = BeautifulSoup(resp.text, "lxml")
            results = []
            for a in soup.select("a.result__a")[:max_results]:
                href = a.get("href", "")
                snippet_el = a.find_parent("div", class_="result__body")
                snippet = ""
                if snippet_el:
                    snip_tag = snippet_el.find("a", class_="result__snippet")
                    if snip_tag:
                        snippet = snip_tag.get_text(strip=True)
                results.append({
                    "title": a.get_text(strip=True),
                    "url": href,
                    "snippet": snippet,
                })
            return results

        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []

    def find_company_domain(self, company_name: str) -> str:
        """
        Search for a company's official website and extract its domain.
        """
        results = self.search(f"{company_name} official website", max_results=3)
        for r in results:
            url = r.get("url", "")
            domain = self._extract_domain(url)
            if domain and self._looks_like_company_domain(domain, company_name):
                return domain
        return ""

    def find_people_at_company(
        self, company_name: str, roles: list[str], max_results: int = 5
    ) -> list[dict]:
        """
        Search for people with specific roles at a company via DuckDuckGo.
        Returns list of {'name': ..., 'title': ..., 'source_url': ...}.
        """
        role_query = " OR ".join(f'"{r}"' for r in roles[:3])
        query = f'site:linkedin.com "{company_name}" ({role_query})'
        results = self.search(query, max_results=max_results)

        people = []
        for r in results:
            name, title = self._parse_linkedin_title(r.get("title", ""))
            if name:
                people.append({
                    "name": name,
                    "title": title,
                    "source_url": r.get("url", ""),
                    "snippet": r.get("snippet", ""),
                    "source": "duckduckgo",
                })
        return people

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_domain(url: str) -> str:
        try:
            if "://" not in url:
                url = "https://" + url
            p = urlparse(url)
            domain = re.sub(r"^www\.", "", p.netloc)
            return domain.split("/")[0]
        except Exception:
            return ""

    @staticmethod
    def _looks_like_company_domain(domain: str, company_name: str) -> bool:
        """Heuristic: check if the domain relates to the company name."""
        company_slug = re.sub(r"[^a-z0-9]", "", company_name.lower())
        domain_root = domain.split(".")[0]
        return (
            company_slug in domain_root
            or domain_root in company_slug
            or len(company_slug) <= 3  # short names like IBM, SAP
        )

    @staticmethod
    def _parse_linkedin_title(title: str) -> tuple[str, str]:
        """
        Parse a LinkedIn search result title like 'John Doe - HR Manager at Acme | LinkedIn'
        into (name, title).
        """
        title = re.sub(r"\s*\|?\s*LinkedIn\s*$", "", title, flags=re.IGNORECASE).strip()
        # Common pattern: "Name - Title at Company"
        m = re.match(r"^(.+?)\s*[-–]\s*(.+?)(?:\s+at\s+.+)?$", title)
        if m:
            return m.group(1).strip(), m.group(2).strip()
        return "", ""
