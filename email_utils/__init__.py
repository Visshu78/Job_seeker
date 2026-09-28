"""
Email Utils package.
"""
from .patterns import EmailPatternGenerator
from .smtp_verifier import SMTPVerifier

__all__ = ["EmailPatternGenerator", "SMTPVerifier"]
