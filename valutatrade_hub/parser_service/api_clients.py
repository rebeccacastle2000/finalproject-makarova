"""Клиенты для работы с внешними API получения курсов валют."""

from abc import ABC, abstractmethod

import requests

from valutatrade_hub.core.exceptions import ApiRequestError

from .config import config


class BaseApiClient(ABC):
    """Абстрактный базовый класс для клиентов API."""

    @abstractmethod
    def fetch_rates(self) -> dict[str, float]:
        """Получение курсов валют.

        Returns:
            Словарь в формате {"Код_валюты": курс}
        """
        pass


class CoinGeckoClient(BaseApiClient):
    """Клиент для работы с CoinGecko API (криптовалюты)."""

    def __init__(self):
        self.base_url = config.COINGECKO_URL
        self.timeout = config.REQUEST_TIMEOUT

    def fetch_rates(self) -> dict[str, float]:
        """Получение курсов криптовалют к базовой валюте (USD).

        Returns:
            Словарь в формате {"BTC_USD": 59337.21, "ETH_USD": 3720.00, ...}
        """
        try:
            url = config.get_coingecko_url()

            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            rates = {}

            # Преобразуем ответ в унифицированный формат
            for code, coin_id in config.CRYPTO_ID_MAP.items():
                if coin_id in data and config.BASE_CURRENCY.lower() in data[coin_id]:
                    rate = data[coin_id][config.BASE_CURRENCY.lower()]
                    pair = f"{code}_{config.BASE_CURRENCY}"
                    rates[pair] = float(rate)

            return rates

        except requests.exceptions.Timeout:
            raise ApiRequestError(
                f"Таймаут запроса к CoinGecko (ожидание более {self.timeout} сек)"
            ) from None
        except requests.exceptions.ConnectionError:
            raise ApiRequestError("Ошибка подключения к CoinGecko API") from None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise ApiRequestError(
                    "Превышен лимит запросов к CoinGecko (429 Too Many Requests)"
                ) from e
            raise ApiRequestError(f"HTTP ошибка CoinGecko: {e.response.status_code}") from e
        except Exception as e:
            raise ApiRequestError(f"Неизвестная ошибка при запросе к CoinGecko: {str(e)}") from e


class ExchangeRateApiClient(BaseApiClient):
    """Клиент для работы с ExchangeRate-API (фиатные валюты)."""

    def __init__(self):
        self.base_url = config.EXCHANGERATE_API_URL
        self.api_key = config.EXCHANGERATE_API_KEY
        self.timeout = config.REQUEST_TIMEOUT

    def fetch_rates(self) -> dict[str, float]:
        """Получение курсов фиатных валют к базовой валюте (USD).

        Returns:
            Словарь в формате {"EUR_USD": 1.0786, "GBP_USD": 1.27, ...}
        """
        if not self.api_key or self.api_key == "YOUR_API_KEY_HERE":
            raise ApiRequestError(
                "API ключ для ExchangeRate-API не настроен. "
                "Добавьте ключ в файл .env: EXCHANGERATE_API_KEY=ваш_ключ"
            ) from None

        try:
            url = config.get_exchangerate_url()

            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            # Проверяем успешность ответа
            if data.get("result") != "success":
                error_msg = data.get("error-type", "Неизвестная ошибка API")
                raise ApiRequestError(f"Ошибка ExchangeRate-API: {error_msg}") from None

            rates = {}
            base_currency = config.BASE_CURRENCY

            # Преобразуем курсы в унифицированный формат
            for currency_code in config.FIAT_CURRENCIES:
                if currency_code in data.get("conversion_rates", {}):
                    # ExchangeRate-API возвращает: 1 USD = X единиц валюты
                    # Нам нужно: 1 единица валюты = Y USD → Y = 1 / X
                    inverse_rate = 1.0 / data["conversion_rates"][currency_code]
                    pair = f"{currency_code}_{base_currency}"
                    rates[pair] = float(inverse_rate)

            return rates

        except requests.exceptions.Timeout:
            raise ApiRequestError(
                f"Таймаут запроса к ExchangeRate-API (ожидание более {self.timeout} сек)"
            ) from None
        except requests.exceptions.ConnectionError:
            raise ApiRequestError("Ошибка подключения к ExchangeRate-API") from None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise ApiRequestError(
                    "Неверный API ключ ExchangeRate-API (401 Unauthorized)"
                ) from e
            elif e.response.status_code == 429:
                raise ApiRequestError(
                    "Превышен лимит запросов к ExchangeRate-API (429 Too Many Requests)"
                ) from e
            raise ApiRequestError(f"HTTP ошибка ExchangeRate-API: {e.response.status_code}") from e
        except Exception as e:
            raise ApiRequestError(
                f"Неизвестная ошибка при запросе к ExchangeRate-API: {str(e)}"
            ) from e
