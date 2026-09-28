"""
Email Pattern Generator — generates likely email addresses from a name + domain
using the most common corporate email formats, ranked by real-world prevalence.
"""
import re
import unicodedata


# Ordered by real-world frequency (Hunter.io 2024 data)
PATTERNS = [
    ("{first}.{last}@{domain}",     0.42),
    ("{first}@{domain}",            0.18),
    ("{f}{last}@{domain}",          0.10),
    ("{first}{last}@{domain}",      0.09),
    ("{first}_{last}@{domain}",     0.06),
    ("{f}.{last}@{domain}",         0.05),
    ("{last}.{first}@{domain}",     0.03),
    ("{last}@{domain}",             0.02),
    ("{first}{l}@{domain}",         0.02),
    ("{first}-{last}@{domain}",     0.01),
    ("{f}{l}@{domain}",             0.01),
    ("{last}{first}@{domain}",      0.01),
]


class EmailPatternGenerator:
    """
    Generates a ranked list of email candidates for a person at a company.
    Returns (email, confidence) tuples sorted by likelihood.
    """

    def generate(self, first: str, last: str, domain: str) -> list[tuple[str, float]]:
        """
        Generate email candidates for a person.
        Returns sorted list of (email, confidence) tuples.
        """
        first = self._normalize(first)
        last = self._normalize(last)
        domain = domain.lower().strip()

        if not first or not domain:
            return []

        candidates = []
        for pattern, confidence in PATTERNS:
            email = self._apply_pattern(pattern, first, last, domain)
            if email and self._is_valid_format(email):
                candidates.append((email, confidence))

        # Deduplicate while preserving order
        seen = set()
        result = []
        for email, conf in candidates:
            if email not in seen:
                seen.add(email)
                result.append((email, conf))

        return result

    def guess_pattern(self, known_emails: list[str], domain: str) -> str:
        """
        Given a list of known emails at a domain, infer the company's pattern.
        Useful for Hunter.io domain-search results.
        """
        pattern_votes: dict[str, int] = {}
        for email in known_emails:
            local = email.split("@")[0]
            matched = self._match_pattern(local)
            if matched:
                pattern_votes[matched] = pattern_votes.get(matched, 0) + 1

        if not pattern_votes:
            return "{first}.{last}"
        return max(pattern_votes, key=lambda k: pattern_votes[k])

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize(name: str) -> str:
        """Lowercase, remove accents, strip non-alpha characters."""
        nfkd = unicodedata.normalize("NFKD", name)
        ascii_name = nfkd.encode("ascii", "ignore").decode("ascii")
        return re.sub(r"[^a-z]", "", ascii_name.lower())

    @staticmethod
    def _apply_pattern(pattern: str, first: str, last: str, domain: str) -> str:
        f = first[0] if first else ""
        l = last[0] if last else ""
        return (
            pattern
            .replace("{first}", first)
            .replace("{last}", last)
            .replace("{f}", f)
            .replace("{l}", l)
            .replace("{domain}", domain)
        )

    @staticmethod
    def _is_valid_format(email: str) -> bool:
        return bool(re.match(r"^[a-z0-9._+-]+@[a-z0-9.-]+\.[a-z]{2,}$", email))

    @staticmethod
    def _match_pattern(local: str) -> str:
        """Infer which pattern a local part likely comes from."""
        patterns = {
            r"^([a-z]+)\.([a-z]+)$": "{first}.{last}",
            r"^([a-z]+)$":           "{first}",
            r"^([a-z])([a-z]+)$":   "{f}{last}",
            r"^([a-z]+)([a-z]+)$":  "{first}{last}",
            r"^([a-z]+)_([a-z]+)$": "{first}_{last}",
        }
        for regex, pname in patterns.items():
            if re.match(regex, local):
                return pname
        return ""
