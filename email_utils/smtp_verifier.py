"""
SMTP Email Verifier — validates emails without sending a message.
Uses DNS MX lookup + SMTP RCPT TO handshake.
Free, no API key required.

Limitations:
- Some servers use catch-all (accept all addresses)
- Some block SMTP verification (Gmail, Outlook)
- Results should be treated as probabilistic, not definitive
"""
import socket
import smtplib
import dns.resolver
from utils.logger import get_logger
from utils.rate_limiter import rate_limiter

logger = get_logger("smtp-verifier")

# Known catch-all / unreliable domains
UNVERIFIABLE_DOMAINS = {
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
    "icloud.com", "protonmail.com", "aol.com", "live.com",
}

# Cache results to avoid re-verifying
_cache: dict[str, dict] = {}

# Cache MX lookups
_mx_cache: dict[str, str] = {}


class SMTPVerifier:
    """
    Verifies email deliverability via SMTP RCPT TO without sending mail.
    """

    TIMEOUT = 10  # seconds
    FROM_EMAIL = "verify@hr-finder.local"

    def verify(self, email: str) -> dict:
        """
        Verify an email address. Returns:
        {
            'valid': bool,
            'type': 'valid' | 'catch_all' | 'invalid' | 'unknown',
            'reason': str,
        }
        """
        if not email or "@" not in email:
            return {"valid": False, "type": "invalid", "reason": "Malformed email"}

        if email in _cache:
            return _cache[email]

        domain = email.split("@")[1].lower()

        # Skip known personal/unreliable domains
        if domain in UNVERIFIABLE_DOMAINS:
            result = {"valid": True, "type": "unknown", "reason": "Personal domain — unverifiable"}
            _cache[email] = result
            return result

        # Step 1: DNS MX lookup
        mx_host = self._get_mx(domain)
        if not mx_host:
            result = {"valid": False, "type": "invalid", "reason": "No MX record found"}
            _cache[email] = result
            return result

        # Step 2: SMTP handshake
        result = self._smtp_check(email, mx_host)
        _cache[email] = result
        return result

    def verify_batch(self, emails: list[str]) -> dict[str, dict]:
        """Verify a list of emails. Returns {email: result} dict."""
        return {email: self.verify(email) for email in emails}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_mx(self, domain: str) -> str:
        if domain in _mx_cache:
            return _mx_cache[domain]
        try:
            records = dns.resolver.resolve(domain, "MX", lifetime=5)
            mx = min(records, key=lambda r: r.preference)
            host = str(mx.exchange).rstrip(".")
            _mx_cache[domain] = host
            return host
        except Exception as e:
            logger.debug(f"MX lookup failed for {domain}: {e}")
            _mx_cache[domain] = ""
            return ""

    def _smtp_check(self, email: str, mx_host: str) -> dict:
        """Perform SMTP RCPT TO check."""
        rate_limiter.wait("free_tools")
        try:
            with smtplib.SMTP(timeout=self.TIMEOUT) as smtp:
                smtp.connect(mx_host, 25)
                smtp.ehlo_or_helo_if_needed()
                smtp.mail(self.FROM_EMAIL)
                code, message = smtp.rcpt(email)

                if code == 250:
                    return {"valid": True, "type": "valid", "reason": "SMTP accepted"}
                elif code == 451:
                    # Could be catch-all or temp failure
                    return {"valid": True, "type": "catch_all", "reason": "Temp defer — likely catch-all"}
                elif code in (550, 551, 553):
                    return {"valid": False, "type": "invalid", "reason": f"SMTP rejected: {code}"}
                else:
                    return {"valid": True, "type": "unknown", "reason": f"SMTP code: {code}"}

        except smtplib.SMTPConnectError:
            return {"valid": True, "type": "unknown", "reason": "SMTP port 25 blocked"}
        except socket.timeout:
            return {"valid": True, "type": "unknown", "reason": "SMTP timeout"}
        except Exception as e:
            logger.debug(f"SMTP check error for {email}: {e}")
            return {"valid": True, "type": "unknown", "reason": f"Error: {str(e)[:80]}"}
