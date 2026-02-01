"""Конфигурация сервиса парсинга курсов валют."""

import os
from dataclasses import dataclass, field


@dataclass
class ParserConfig:
    """Конфигурация парсера валютных курсов."""

    # ========== API-ключи ==========
    EXCHANGERATE_API_KEY: str = field(
        default_factory=lambda: os.getenv("EXCHANGERATE_API_KEY", "7ed19eee89d34a62b962ee63")
    )

    # ========== Эндпоинты ==========
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"

    # ========== Списки валют ==========
    BASE_CURRENCY: str = "USD"

    FIAT_CURRENCIES: tuple[str, ...] = ("EUR", "GBP", "RUB", "JPY", "CHF", "CNY", "AUD")

    CRYPTO_CURRENCIES: tuple[str, ...] = ("BTC", "ETH", "SOL", "XRP", "DOGE", "ADA")

    CRYPTO_ID_MAP: dict[str, str] = field(
        default_factory=lambda: {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana",
            "XRP": "ripple",
            "DOGE": "dogecoin",
            "ADA": "cardano",
        }
    )

    # ========== Пути к файлам ==========
    RATES_FILE_PATH: str = "data/rates.json"
    HISTORY_FILE_PATH: str = "data/exchange_rates.json"

    # ========== Сетевые параметры ==========
    REQUEST_TIMEOUT: int = 10
    MAX_RETRIES: int = 3

    # ========== Кэширование ==========
    CACHE_TTL_SECONDS: int = 300

    def get_coingecko_url(self) -> str:
        """Формирует полный URL для запроса к CoinGecko."""
        ids = ",".join(self.CRYPTO_ID_MAP.values())
        return f"{self.COINGECKO_URL}?ids={ids}&vs_currencies={self.BASE_CURRENCY.lower()}"

    def get_exchangerate_url(self) -> str:
        """Формирует полный URL для запроса к ExchangeRate-API."""
        return (
            f"{self.EXCHANGERATE_API_URL}/{self.EXCHANGERATE_API_KEY}/latest/{self.BASE_CURRENCY}"
        )

    def get_crypto_id(self, currency_code: str) -> str:
        """Возвращает внутренний идентификатор криптовалюты для CoinGecko."""
        return self.CRYPTO_ID_MAP.get(currency_code, currency_code.lower())


# Глобальный экземпляр конфигурации
config = ParserConfig()
