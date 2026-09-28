"""
Scheduler — runs the pipeline automatically on a schedule.
Supports daily, weekly, and monthly frequencies.
"""
import threading
import time
from datetime import datetime
from pathlib import Path
from utils.logger import get_logger
from utils.config_loader import load_config

logger = get_logger("scheduler")


class Scheduler:
    """
    Background scheduler that triggers the pipeline at configured intervals.
    """

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._running = False

    def start(self) -> None:
        """Start the scheduler in a background thread."""
        config = load_config(self.config_path)
        sched_cfg = config.get("schedule", {})

        if not sched_cfg.get("enabled", False):
            logger.info("Scheduler is disabled in config.")
            return

        self._stop_event.clear()
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="scheduler")
        self._thread.start()
        logger.info(
            f"[green]Scheduler started[/green] — "
            f"frequency: {sched_cfg.get('frequency', 'weekly')}, "
            f"time: {sched_cfg.get('time', '09:00')}"
        )

    def stop(self) -> None:
        """Stop the scheduler."""
        self._stop_event.set()
        self._running = False
        logger.info("Scheduler stopped.")

    def is_running(self) -> bool:
        return self._running

    def run_now(self, config_path: str = None) -> None:
        """Trigger an immediate pipeline run."""
        self._execute(config_path or self.config_path)

    # ------------------------------------------------------------------
    # Internal loop
    # ------------------------------------------------------------------

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            config = load_config(self.config_path)
            sched_cfg = config.get("schedule", {})
            input_file = sched_cfg.get("input_file", "input/companies.csv")

            if self._should_run_now(sched_cfg):
                logger.info("[bold cyan]Scheduled run triggered[/bold cyan]")
                self._execute(self.config_path, input_file)

            # Check every minute
            self._stop_event.wait(60)

    def _should_run_now(self, sched_cfg: dict) -> bool:
        now = datetime.now()
        freq = sched_cfg.get("frequency", "weekly")
        run_time = sched_cfg.get("time", "09:00")
        h, m = map(int, run_time.split(":"))

        if now.hour != h or now.minute != m:
            return False

        if freq == "daily":
            return True
        elif freq == "weekly":
            target_day = sched_cfg.get("day_of_week", "monday").lower()
            day_map = {
                "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                "friday": 4, "saturday": 5, "sunday": 6
            }
            return now.weekday() == day_map.get(target_day, 0)
        elif freq == "monthly":
            target_day = sched_cfg.get("day_of_month", 1)
            return now.day == target_day

        return False

    @staticmethod
    def _execute(config_path: str, input_file: str = None) -> None:
        """Execute a full pipeline run."""
        try:
            from pipeline import Pipeline
            config = load_config(config_path)
            if not input_file:
                input_file = config.get("schedule", {}).get("input_file", "input/companies.csv")

            if not Path(input_file).exists():
                logger.error(f"Input file not found: {input_file}")
                return

            pipe = Pipeline(config)
            contacts = pipe.run_from_csv(input_file)
            logger.info(f"Scheduled run complete: {len(contacts)} contacts found")
        except Exception as ex:
            logger.error(f"Scheduled run failed: {ex}")
