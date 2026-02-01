#!/usr/bin/env python3
"""Точка входа в приложение валютного кошелька."""

from valutatrade_hub.cli.interface import CLI


def main():
    """Запуск CLI интерфейса."""
    cli = CLI()
    cli.run()


if __name__ == "__main__":
    main()
