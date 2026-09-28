"""
Config loader — reads, validates, and saves config.yaml.
"""
import os
import yaml
from pathlib import Path
from copy import deepcopy

ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "config.yaml"


def load_config(path: str | Path = CONFIG_PATH) -> dict:
    """Load and return the YAML config as a dict."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_config(config: dict, path: str | Path = CONFIG_PATH) -> None:
    """Write a config dict back to the YAML file."""
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def get_active_roles(config: dict) -> list[str]:
    """Flatten all active preset roles + any custom roles into a list."""
    search = config.get("search", {})
    presets = search.get("role_presets", {})
    active = search.get("active_presets", [])
    roles = []
    for preset_name in active:
        roles.extend(presets.get(preset_name, []))
    roles.extend(presets.get("custom", []))
    return list(dict.fromkeys(roles))  # deduplicate, preserve order


def get_enabled_tools(config: dict) -> list[str]:
    """Return list of enabled tool names in waterfall order."""
    tools = config.get("tools", {})
    order = config.get("pipeline", {}).get("waterfall_order", [])
    return [t for t in order if tools.get(t, {}).get("enabled", False)]


def get_tool_config(config: dict, tool_name: str) -> dict:
    """Return the config block for a specific tool."""
    return config.get("tools", {}).get(tool_name, {})
