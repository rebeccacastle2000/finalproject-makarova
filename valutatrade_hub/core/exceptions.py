"""Пользовательские исключения для бизнес-логики."""


class InsufficientFundsError(Exception):
    """Недостаточно средств на кошельке."""

    def __init__(self, currency_code: str, available: float, required: float):
        super().__init__(
            f"Недостаточно средств: доступно {available:.4f} {currency_code}, "
            f"требуется {required:.4f} {currency_code}"
        )
        self.currency_code = currency_code
        self.available = available
        self.required = required


class CurrencyNotFoundError(Exception):
    """Валюта не найдена в системе."""

    def __init__(self, code: str):
        super().__init__(f"Неизвестная валюта '{code}'")
        self.code = code


class ApiRequestError(Exception):
    """Ошибка при обращении к внешнему API."""

    def __init__(self, reason: str):
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")
        self.reason = reason


class UserNotFoundError(Exception):
    """Пользователь не найден."""

    def __init__(self, username: str):
        super().__init__(f"Пользователь '{username}' не найден")
        self.username = username


class AuthenticationError(Exception):
    """Ошибка аутентификации."""

    def __init__(self, username: str):
        super().__init__(f"Неверный пароль для пользователя '{username}'")
        self.username = username


class WalletNotFoundError(Exception):
    """Кошелёк не найден."""

    def __init__(self, currency_code: str):
        super().__init__(
            f"У вас нет кошелька '{currency_code}'. "
            f"Добавьте валюту: она создаётся автоматически при первой покупке."
        )
        self.currency_code = currency_code


class ValidationError(Exception):
    """Ошибка валидации входных данных."""

    def __init__(self, field: str, message: str):
        super().__init__(f"Ошибка валидации поля '{field}': {message}")
        self.field = field
        self.message = message
