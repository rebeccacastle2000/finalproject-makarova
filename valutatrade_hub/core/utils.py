"""Вспомогательные функции и утилиты для бизнес-логики."""

from datetime import datetime
from typing import Optional

from .currencies import CurrencyNotFoundError, get_currency
from .exceptions import ValidationError


def validate_currency_code(code: str) -> str:
    code = code.strip().upper()
    try:
        get_currency(code)
        return code
    except CurrencyNotFoundError as e:
        raise ValidationError("currency_code", str(e)) from e


def validate_positive_amount(amount: float, field_name: str = "amount") -> float:
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise ValidationError(field_name, "должен быть числом") from None

    if amount <= 0:
        raise ValidationError(field_name, "должен быть положительным числом")
    return amount


def get_exchange_rate(from_code: str, to_code: str, rates_cache: Optional[dict] = None) -> float:
    from_code = from_code.upper()
    to_code = to_code.upper()

    if from_code == to_code:
        return 1.0

    if rates_cache is None:
        stub_rates = {
            "USD_EUR": 0.927,
            "EUR_USD": 1.0786,
            "USD_RUB": 98.43,
            "RUB_USD": 0.01016,
            "USD_BTC": 1.685e-5,
            "BTC_USD": 59337.21,
            "USD_ETH": 0.0002688,
            "ETH_USD": 3720.00,
            "USD_SOL": 0.00687,
            "SOL_USD": 145.50,
            "USD_XRP": 1.724,
            "XRP_USD": 0.58,
            "USD_GBP": 0.787,
            "GBP_USD": 1.27,
            "USD_JPY": 149.25,
            "JPY_USD": 0.0067,
        }
        pair = f"{from_code}_{to_code}"
        if pair in stub_rates:
            return stub_rates[pair]
        reverse_pair = f"{to_code}_{from_code}"
        if reverse_pair in stub_rates:
            return 1.0 / stub_rates[reverse_pair]
        raise ValueError(f"Курс {from_code}→{to_code} недоступен")

    pair = f"{from_code}_{to_code}"
    if pair in rates_cache and "rate" in rates_cache[pair]:
        return rates_cache[pair]["rate"]

    reverse_pair = f"{to_code}_{from_code}"
    if reverse_pair in rates_cache and "rate" in rates_cache[reverse_pair]:
        return 1.0 / rates_cache[reverse_pair]["rate"]

    raise ValueError(f"Курс {from_code}→{to_code} недоступен")


def is_rate_cache_fresh(updated_at: str, ttl_seconds: int = 300) -> bool:
    try:
        updated_dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        delta = datetime.now(updated_dt.tzinfo) - updated_dt
        return delta.total_seconds() < ttl_seconds
    except (ValueError, TypeError):
        return False


def format_currency_amount(amount: float, currency_code: str) -> str:
    crypto_codes = {"BTC", "ETH", "SOL", "XRP"}
    if currency_code in crypto_codes:
        return f"{amount:.6f}"
    return f"{amount:.2f}"
