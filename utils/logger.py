"""
Logger utility - rich-powered colored logging.
"""
import sys
import logging
from rich.logging import RichHandler
from rich.console import Console

# Always use utf-8 output to prevent Windows cp1252 encoding errors
console = Console(file=sys.stdout, highlight=False, markup=True, force_terminal=False, legacy_windows=False)

def get_logger(name: str = "hr-finder") -> logging.Logger:
    """Return a configured logger with rich formatting."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=False, markup=True, show_path=True)],
    )
    logger = logging.getLogger(name)
    return logger
