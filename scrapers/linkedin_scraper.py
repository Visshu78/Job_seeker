"""
LinkedIn Scraper — uses Playwright (headless browser) to extract
HR contacts from LinkedIn people search.

⚠️  WARNING: This scraping violates LinkedIn's Terms of Service.
Use responsibly and only enable in config if you accept the risk.
Requires: playwright install chromium
"""
import time
import random
from utils.logger import get_logger
from utils.rate_limiter import rate_limiter

logger = get_logger("linkedin-scraper")


class LinkedInScraper:
    """
    Headless browser scraper for LinkedIn people search.
    Requires Playwright + a LinkedIn session cookie or credentials.
    """

    def __init__(self, li_at_cookie: str = ""):
        self.li_at_cookie = li_at_cookie
        self._browser = None
        self._page = None

    def find_people(
        self,
        company_name: str,
        roles: list[str],
        max_results: int = 5,
    ) -> list[dict]:
        """
        Search LinkedIn for people with given roles at the company.
        Returns list of contact dicts.
        """
        if not self.li_at_cookie:
            logger.warning(
                "[yellow]LinkedIn scraper: no li_at cookie configured. "
                "Add it to config.yaml under tools.free_tools.li_at_cookie[/yellow]"
            )
            return []

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.error(
                "[red]Playwright not installed. Run: pip install playwright && playwright install chromium[/red]"
            )
            return []

        results = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/122.0.0.0 Safari/537.36"
                    )
                )
                # Set LinkedIn session cookie
                context.add_cookies([
                    {
                        "name": "li_at",
                        "value": self.li_at_cookie,
                        "domain": ".linkedin.com",
                        "path": "/",
                    }
                ])
                page = context.new_page()

                for role in roles[:2]:  # limit roles to reduce ban risk
                    rate_limiter.wait("linkedin")
                    url = self._build_search_url(company_name, role)
                    logger.info(f"[blue]LinkedIn[/blue] searching: {role} at {company_name}")
                    page.goto(url, wait_until="networkidle", timeout=30000)
                    time.sleep(random.uniform(2, 4))

                    people = self._extract_results(page)
                    results.extend(people)
                    if len(results) >= max_results:
                        break

                browser.close()
        except Exception as e:
            logger.error(f"LinkedIn scraper error: {e}")

        return results[:max_results]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_search_url(company: str, role: str) -> str:
        from urllib.parse import quote_plus
        return (
            f"https://www.linkedin.com/search/results/people/"
            f"?keywords={quote_plus(role)}"
            f"&origin=GLOBAL_SEARCH_HEADER"
            f"&company={quote_plus(company)}"
        )

    @staticmethod
    def _extract_results(page) -> list[dict]:
        """Parse people cards from a LinkedIn search results page."""
        results = []
        try:
            cards = page.query_selector_all(".entity-result__item")
            for card in cards:
                name_el = card.query_selector(".entity-result__title-text a span[aria-hidden='true']")
                title_el = card.query_selector(".entity-result__primary-subtitle")
                profile_el = card.query_selector(".entity-result__title-text a")

                name = name_el.inner_text().strip() if name_el else ""
                title = title_el.inner_text().strip() if title_el else ""
                profile_url = profile_el.get_attribute("href") if profile_el else ""

                if name:
                    results.append({
                        "name": name,
                        "title": title,
                        "profile_url": profile_url,
                        "source": "linkedin",
                    })
        except Exception as e:
            logger.debug(f"LinkedIn result extraction error: {e}")
        return results
