#!/usr/bin/env python3
"""Точка входа в приложение валютного кошелька."""

from valutatrade_hub.cli.interface import CLI
from valutatrade_hub.parser_service.scheduler import Scheduler


def main():
    """Запуск CLI интерфейса."""
    cli = CLI()

    # Запуск фонового обновления курсов каждые 5 минут
    scheduler = Scheduler(interval_seconds=300)
    scheduler.start()

    try:
        cli.run()
    finally:
        scheduler.stop()


if __name__ == "__main__":
    main()
