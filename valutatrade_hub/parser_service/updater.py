"""Координация обновления курсов валют из внешних источников."""

import logging
from datetime import datetime, timezone
from typing import Any

from .api_clients import CoinGeckoClient, ExchangeRateApiClient
from .storage import RatesStorage


class RatesUpdater:
    """Координатор обновления курсов валют."""

    def __init__(self):
        self.storage = RatesStorage()
        self.coingecko_client = CoinGeckoClient()
        self.exchangerate_client = ExchangeRateApiClient()
        self.logger = logging.getLogger(__name__)

    def run_update(self, source: str | None = None) -> dict[str, Any]:
        """Выполнить обновление курсов валют.
        Args:
            source: Опционально — обновить только указанный источник ('coingecko' или 'exchangerate')
        Returns:
            Словарь с результатами обновления
        """
        self.logger.info("Starting rates update...")
        results = {
            "success": True,
            "updated_pairs": {},
            "errors": [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Обновление криптовалют
        if source is None or source == "coingecko":
            try:
                self.logger.info("Fetching from CoinGecko...")
                crypto_rates = self.coingecko_client.fetch_rates()
                for pair, rate in crypto_rates.items():
                    self.storage.append_to_history(pair, rate, "CoinGecko")
                results["updated_pairs"].update(crypto_rates)
                self.logger.info(f"OK ({len(crypto_rates)} rates)")
            except Exception as e:
                results["success"] = False
                results["errors"].append(f"CoinGecko: {str(e)}")
                self.logger.error(f"Failed to fetch from CoinGecko: {e}")

        # Обновление фиатных валют
        if source is None or source == "exchangerate":
            try:
                self.logger.info("Fetching from ExchangeRate-API...")
                fiat_rates = self.exchangerate_client.fetch_rates()
                for pair, rate in fiat_rates.items():
                    self.storage.append_to_history(pair, rate, "ExchangeRate-API")
                results["updated_pairs"].update(fiat_rates)
                self.logger.info(f"OK ({len(fiat_rates)} rates)")
            except Exception as e:
                results["success"] = False
                results["errors"].append(f"ExchangeRate-API: {str(e)}")
                self.logger.error(f"Failed to fetch from ExchangeRate-API: {e}")

        # Сохранение в кэш
        if results["updated_pairs"]:
            source_name = "ParserService"
            if len(results["errors"]) == 1:
                source_name = (
                    "CoinGecko"
                    if "ExchangeRate-API" in results["errors"][0]
                    else "ExchangeRate-API"
                )
            elif len(results["errors"]) == 0:
                source_name = "CoinGecko+ExchangeRate-API"

            self.storage.save_current_rates(results["updated_pairs"], source_name)
            self.logger.info(
                f"Writing {len(results['updated_pairs'])} rates to {self.storage.rates_path}"
            )

        self.logger.info("Update completed")
        return results
