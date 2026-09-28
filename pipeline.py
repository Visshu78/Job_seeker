"""
Pipeline — the main orchestration engine.
Coordinates domain resolution, people discovery, and email enrichment
across all configured tools in waterfall order.
"""
import csv
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

from scrapers.domain_resolver import DomainResolver
from enrichers import build_enrichers
from enrichers.base import Contact
from output.exporter import Exporter
from utils.config_loader import get_active_roles, get_enabled_tools
from utils.logger import get_logger

logger = get_logger("pipeline")


class Pipeline:
    """
    Main orchestration class that runs the full email-finding pipeline.
    """

    def __init__(self, config: dict):
        self.config = config
        self.pipeline_cfg = config.get("pipeline", {})
        self.search_cfg = config.get("search", {})
        self.roles = get_active_roles(config)
        self.max_per_company = self.search_cfg.get("max_per_company", 5)
        self.stop_on_first = self.pipeline_cfg.get("stop_on_first_result", False)
        self.verify_emails = self.pipeline_cfg.get("verify_emails", True)
        self.min_confidence = self.pipeline_cfg.get("min_confidence", 0.5)
        self.max_workers = self.pipeline_cfg.get("max_workers", 3)

        self._domain_resolver = DomainResolver()
        self._enrichers = build_enrichers(config)
        self._exporter = Exporter(config.get("output", {}))

        # Progress callback for the web dashboard
        self._progress_cb: Callable | None = None
        self._status: dict = {"running": False, "progress": 0, "total": 0, "log": []}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_progress_callback(self, cb: Callable) -> None:
        """Register a callback(event: str, data: dict) for real-time progress."""
        self._progress_cb = cb

    def run_from_csv(self, csv_path: str) -> list[Contact]:
        """Load companies from a CSV file and run the pipeline."""
        companies = self._load_csv(csv_path)
        return self.run(companies)

    def run(self, companies: list[dict]) -> list[Contact]:
        """
        Run pipeline on a list of company dicts.
        Each dict: {company_name, website (optional), notes (optional)}
        Returns all discovered contacts.
        """
        if not self._enrichers:
            logger.warning(
                "[yellow]⚠ No tools enabled! "
                "Enable at least 'free_tools' in config.yaml[/yellow]"
            )

        all_contacts: list[Contact] = []
        self._status.update({"running": True, "progress": 0, "total": len(companies), "log": []})
        self._emit("start", {"total": len(companies), "roles": self.roles})

        logger.info(f"\n[bold cyan]━━ Pipeline Starting ━━[/bold cyan]")
        logger.info(f"  Companies : {len(companies)}")
        logger.info(f"  Roles     : {', '.join(self.roles[:5])}{'...' if len(self.roles) > 5 else ''}")
        logger.info(f"  Tools     : {[e.tool_name for e in self._enrichers]}")
        logger.info(f"  Max/company: {self.max_per_company}\n")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._process_company, comp): comp
                for comp in companies
            }
            for i, future in enumerate(as_completed(futures), 1):
                comp = futures[future]
                try:
                    contacts = future.result()
                    all_contacts.extend(contacts)
                    self._status["progress"] = i
                    self._emit("company_done", {
                        "company": comp.get("company_name", ""),
                        "contacts_found": len(contacts),
                        "progress": i,
                        "total": len(companies),
                    })
                except Exception as ex:
                    logger.error(f"Error processing {comp.get('company_name', '?')}: {ex}")

        # Export results
        paths = self._exporter.export(all_contacts)

        self._status["running"] = False
        self._emit("done", {
            "total_contacts": len(all_contacts),
            "output_paths": paths,
        })

        logger.info(f"\n[bold green]━━ Pipeline Complete ━━[/bold green]")
        logger.info(f"  Total contacts found: {len(all_contacts)}")

        return all_contacts

    def get_status(self) -> dict:
        return self._status

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _process_company(self, comp: dict) -> list[Contact]:
        """Full pipeline for a single company."""
        name = comp.get("company_name", "").strip()
        website = comp.get("website", "").strip()

        if not name:
            return []

        # Step 1: Resolve domain
        domain = self._domain_resolver.resolve(name, website)
        if not domain:
            logger.warning(f"[yellow]Skipping {name}: domain not found[/yellow]")
            return []

        logger.info(f"[bold]Processing:[/bold] {name} ({domain})")
        self._log(f"Processing: {name} ({domain})")

        # Step 2: Find people + enrich emails via waterfall
        all_contacts: list[Contact] = []

        for enricher in self._enrichers:
            if not enricher.is_available():
                continue

            try:
                # Find people
                found = enricher.find_people(name, domain, self.roles, self.max_per_company)

                # Enrich emails for contacts missing them
                enriched = []
                for c in found:
                    if not c.email:
                        c = enricher.enrich_email(c)
                    enriched.append(c)

                # Merge with existing (prefer higher confidence)
                all_contacts = self._merge_contacts(all_contacts, enriched)

                if self.stop_on_first and any(c.email for c in all_contacts):
                    break

            except Exception as ex:
                logger.error(f"{enricher.tool_name} error for {name}: {ex}")

        # Step 3: For contacts still missing emails, try free_tools pattern+SMTP
        if self.verify_emails:
            from enrichers.free_tools import FreeToolsEnricher
            free_cfg = self.config.get("tools", {}).get("free_tools", {})
            free_enricher = FreeToolsEnricher(free_cfg)
            for i, c in enumerate(all_contacts):
                if not c.email and c.first_name:
                    all_contacts[i] = free_enricher.enrich_email(c)

        # Step 4: Filter by confidence
        result = [
            c for c in all_contacts
            if c.confidence >= self.min_confidence
        ][:self.max_per_company]

        logger.info(
            f"  [green]→[/green] {name}: {len(result)} contact(s) found "
            f"({'✉ ' + result[0].email if result and result[0].email else 'no emails'})"
        )
        return result

    @staticmethod
    def _merge_contacts(existing: list[Contact], new: list[Contact]) -> list[Contact]:
        """
        Merge two contact lists by name, keeping highest-confidence version.
        """
        index: dict[str, Contact] = {}
        for c in existing:
            key = c.name.lower().strip()
            if key:
                index[key] = c
        for c in new:
            key = c.name.lower().strip()
            if not key:
                existing.append(c)
                continue
            if key not in index or c.confidence > index[key].confidence:
                index[key] = c
        return list(index.values())

    @staticmethod
    def _load_csv(csv_path: str) -> list[dict]:
        """Load companies from a CSV file."""
        companies = []
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Normalize field names
                normalized = {
                    "company_name": row.get("company_name") or row.get("Company") or row.get("name") or "",
                    "website": row.get("website") or row.get("Website") or row.get("domain") or "",
                    "industry": row.get("industry") or row.get("Industry") or "",
                    "notes": row.get("notes") or row.get("Notes") or "",
                }
                if normalized["company_name"]:
                    companies.append(normalized)
        return companies

    def _emit(self, event: str, data: dict) -> None:
        """Emit a progress event to the registered callback."""
        if self._progress_cb:
            try:
                self._progress_cb(event, data)
            except Exception:
                pass

    def _log(self, message: str) -> None:
        self._status["log"].append(message)
        if len(self._status["log"]) > 200:
            self._status["log"] = self._status["log"][-200:]
