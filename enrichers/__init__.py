"""
Enrichers package — all email enrichment tools live here.
Each enricher implements the BaseEnricher interface.
"""
from .base import BaseEnricher, Contact
from .hunter_io import HunterIOEnricher
from .signalhire import SignalHireEnricher
from .apollo_io import ApolloIOEnricher
from .snov_io import SnovIOEnricher
from .rocketreach import RocketReachEnricher
from .contactout import ContactOutEnricher
from .free_tools import FreeToolsEnricher

__all__ = [
    "BaseEnricher",
    "Contact",
    "HunterIOEnricher",
    "SignalHireEnricher",
    "ApolloIOEnricher",
    "SnovIOEnricher",
    "RocketReachEnricher",
    "ContactOutEnricher",
    "FreeToolsEnricher",
]

# Registry — maps config key → enricher class
ENRICHER_REGISTRY: dict[str, type[BaseEnricher]] = {
    "hunter_io":    HunterIOEnricher,
    "signalhire":   SignalHireEnricher,
    "apollo_io":    ApolloIOEnricher,
    "snov_io":      SnovIOEnricher,
    "rocketreach":  RocketReachEnricher,
    "contactout":   ContactOutEnricher,
    "free_tools":   FreeToolsEnricher,
}


def build_enrichers(config: dict) -> list[BaseEnricher]:
    """
    Instantiate all enabled enrichers in waterfall order from the config.
    """
    tools_cfg = config.get("tools", {})
    order = config.get("pipeline", {}).get("waterfall_order", [])
    enrichers = []
    for tool_name in order:
        tool_cfg = tools_cfg.get(tool_name, {})
        if tool_cfg.get("enabled", False):
            cls = ENRICHER_REGISTRY.get(tool_name)
            if cls:
                enrichers.append(cls(tool_cfg))
    return enrichers
