"""
Base Enricher - abstract interface all enrichers must implement.
Also defines the Contact dataclass used throughout the pipeline.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Contact:
    """Represents a discovered person/contact."""
    # Identity
    first_name: str = ""
    last_name: str = ""
    full_name: str = ""
    title: str = ""

    # Company
    company: str = ""
    domain: str = ""

    # Contact Info
    email: str = ""              # primary email
    work_email: str = ""         # company / corporate email
    personal_email: str = ""     # personal email (gmail, yahoo, etc.)
    email_verified: bool = False
    email_type: str = ""         # personal | professional | catch_all | unknown
    phone: str = ""
    linkedin_url: str = ""

    # Metadata
    source: str = ""             # which tool found this
    confidence: float = 0.0     # 0.0 - 1.0
    notes: str = ""
    raw: dict = field(default_factory=dict)  # raw API response

    @property
    def name(self) -> str:
        if self.full_name:
            return self.full_name
        return f"{self.first_name} {self.last_name}".strip()

    def to_dict(self) -> dict:
        pri_email = self.email or self.work_email or self.personal_email
        w_email = self.work_email or (pri_email if self.domain and f"@{self.domain}" in pri_email else "")
        p_email = self.personal_email or (pri_email if any(pri_email.lower().endswith(f"@{d}") for d in ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com", "protonmail.com", "aol.com"]) else "")
        
        return {
            "Name": self.name,
            "First Name": self.first_name,
            "Last Name": self.last_name,
            "Title": self.title,
            "Company": self.company,
            "Domain": self.domain,
            "LinkedIn URL": self.linkedin_url,
            "Work Email": w_email,
            "Personal Email": p_email,
            "Primary Email": pri_email,
            "Email Verified": self.email_verified,
            "Email Type": self.email_type,
            "Phone": self.phone,
            "Source": self.source,
            "Confidence": round(self.confidence, 2),
            "Notes": self.notes,
        }


class BaseEnricher(ABC):
    """Abstract base class for all email enrichment tools."""

    tool_name: str = "base"

    def __init__(self, config: dict):
        self.config = config
        self.api_key = config.get("api_key", "")
        self.daily_limit = config.get("daily_limit", 9999)
        self._call_count = 0

    @abstractmethod
    def find_people(
        self,
        company: str,
        domain: str,
        roles: list[str],
        max_results: int = 5,
    ) -> list[Contact]:
        """
        Search for people at the given company/domain with matching roles.
        Returns a list of Contact objects.
        """

    @abstractmethod
    def enrich_email(self, contact: Contact) -> Contact:
        """
        Given a contact with name + domain, attempt to find/verify their email.
        Returns the same contact, updated with email info.
        """

    def is_available(self) -> bool:
        """Check if this tool still has credits/quota."""
        return self._call_count < self.daily_limit

    def _increment(self) -> None:
        self._call_count += 1

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} calls={self._call_count}/{self.daily_limit}>"
