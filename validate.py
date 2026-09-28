import sys, os
sys.path.insert(0, '.')
from utils.config_loader import load_config, get_active_roles, get_enabled_tools
from enrichers import build_enrichers, ENRICHER_REGISTRY
from email_utils.patterns import EmailPatternGenerator
from email_utils.smtp_verifier import SMTPVerifier
from scrapers.domain_resolver import DomainResolver
from scrapers.duckduckgo import DuckDuckGoSearch
from output.exporter import Exporter
from pipeline import Pipeline
from scheduler import Scheduler

cfg = load_config('config.yaml')
roles = get_active_roles(cfg)
tools = get_enabled_tools(cfg)
gen = EmailPatternGenerator()
candidates = gen.generate('John', 'Smith', 'stripe.com')

print('OK: All imports passed')
print('  Active roles:', len(roles))
print('  Enabled tools:', tools)
print('  Enrichers registered:', list(ENRICHER_REGISTRY.keys()))
print('  Top email pattern:', candidates[0])
print('System ready!')
