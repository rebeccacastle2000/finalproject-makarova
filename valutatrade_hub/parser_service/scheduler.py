"""Планировщик периодического обновления курсов валют."""

import logging
import threading
from typing import Optional

from .updater import RatesUpdater


class Scheduler:
    """Планировщик для периодического запуска обновления курсов."""

    def __init__(self, interval_seconds: int = 300):
        self.interval = interval_seconds
        self.updater = RatesUpdater()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.logger = logging.getLogger(__name__)

    def start(self) -> None:
        """Запуск периодического обновления в фоновом потоке."""
        if self._thread and self._thread.is_alive():
            self.logger.warning("Scheduler already running")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="RatesScheduler")
        self._thread.start()
        self.logger.info(f"Scheduler started (interval: {self.interval} seconds)")

    def stop(self) -> None:
        """Остановка планировщика."""
        if self._thread and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join(timeout=5.0)
            self.logger.info("Scheduler stopped")

    def _run_loop(self) -> None:
        """Основной цикл планировщика."""
        while not self._stop_event.is_set():
            try:
                self.logger.info("Scheduled rates update started")
                result = self.updater.run_update()
                status = "success" if result["success"] else "partial success with errors"
                self.logger.info(
                    f"Scheduled update completed: {status}, {len(result['updated_pairs'])} pairs updated"
                )
            except Exception as e:
                self.logger.error(f"Scheduled update failed: {e}")

            # Ожидание с возможностью прерывания
            self._stop_event.wait(timeout=self.interval)
