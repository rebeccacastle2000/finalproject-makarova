from abc import ABC, abstractmethod

from valutatrade_hub.core.exceptions import CurrencyNotFoundError


class Currency(ABC):
    def __init__(self, name: str, code: str):
        if not name or not name.strip():
            raise ValueError("Имя валюты не может быть пустым")
        if not code or not (2 <= len(code) <= 5) or not code.isalnum():
            raise ValueError(
                "Код валюты должен быть 2-5 символов без пробелов (только буквы/цифры)"
            )
        self.name = name.strip()
        self.code = code.upper()

    @abstractmethod
    def get_display_info(self) -> str:
        pass

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code='{self.code}', name='{self.name}')"


class FiatCurrency(Currency):
    def __init__(self, name: str, code: str, issuing_country: str):
        super().__init__(name, code)
        if not issuing_country or not issuing_country.strip():
            raise ValueError("Страна эмиссии не может быть пустой")
        self.issuing_country = issuing_country.strip()

    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"


class CryptoCurrency(Currency):
    def __init__(self, name: str, code: str, algorithm: str, market_cap: float):
        super().__init__(name, code)
        if not algorithm or not algorithm.strip():
            raise ValueError("Алгоритм не может быть пустым")
        if market_cap < 0:
            raise ValueError("Рыночная капитализация не может быть отрицательной")
        self.algorithm = algorithm.strip()
        self.market_cap = market_cap

    def get_display_info(self) -> str:
        if self.market_cap >= 1e12:
            mcap_str = f"{self.market_cap / 1e12:.2f}T"
        elif self.market_cap >= 1e9:
            mcap_str = f"{self.market_cap / 1e9:.2f}B"
        elif self.market_cap >= 1e6:
            mcap_str = f"{self.market_cap / 1e6:.2f}M"
        else:
            mcap_str = f"{self.market_cap:,.0f}"
        return f"[CRYPTO] {self.code} — {self.name} (Algo: {self.algorithm}, MCAP: {mcap_str})"


_CURRENCY_REGISTRY: dict[str, Currency] = {
    "USD": FiatCurrency("US Dollar", "USD", "United States"),
    "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
    "RUB": FiatCurrency("Russian Ruble", "RUB", "Russia"),
    "GBP": FiatCurrency("British Pound", "GBP", "United Kingdom"),
    "JPY": FiatCurrency("Japanese Yen", "JPY", "Japan"),
    "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 2.8e11),
    "SOL": CryptoCurrency("Solana", "SOL", "Proof of History", 4.5e10),
    "XRP": CryptoCurrency("Ripple", "XRP", "RPCA", 3.2e10),
}


def get_currency(code: str) -> Currency:
    code = code.upper().strip()
    if code not in _CURRENCY_REGISTRY:
        raise CurrencyNotFoundError(code)
    return _CURRENCY_REGISTRY[code]


def get_supported_currencies() -> dict[str, Currency]:
    return _CURRENCY_REGISTRY.copy()
