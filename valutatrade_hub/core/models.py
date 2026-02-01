"""Модели данных приложения с приватными полями и интеграцией валют."""

import hashlib
from datetime import datetime
from typing import Optional

from .currencies import Currency, get_currency
from .exceptions import InsufficientFundsError, WalletNotFoundError


class User:
    """Пользователь системы."""

    def __init__(
        self,
        user_id: int,
        username: str,
        password: str,
        salt: Optional[str] = None,
        registration_date: Optional[datetime] = None,
    ):
        self._user_id = user_id
        self.username = username
        self._salt = salt or self._generate_salt()
        self._hashed_password = self._hash_password(password)
        self._registration_date = registration_date or datetime.now()

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str):
        if not value or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = value.strip()

    @property
    def registration_date(self) -> datetime:
        return self._registration_date

    def _generate_salt(self) -> str:
        """Генерация уникальной соли."""
        import secrets

        return secrets.token_urlsafe(8)

    def _hash_password(self, password: str) -> str:
        """Хеширование пароля с солью."""
        if len(password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
        return hashlib.sha256((password + self._salt).encode()).hexdigest()

    def verify_password(self, password: str) -> bool:
        """Проверка пароля."""
        return self._hash_password(password) == self._hashed_password

    def change_password(self, new_password: str) -> None:
        """Изменение пароля."""
        if len(new_password) < 4:
            raise ValueError("Новый пароль должен быть не короче 4 символов")
        self._hashed_password = self._hash_password(new_password)
        self._salt = self._generate_salt()

    def get_user_info(self) -> dict:
        """Информация о пользователе (без пароля)."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
        }

    def to_dict(self) -> dict:
        """Сериализация в словарь."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Десериализация пользователя из словаря без повторного хеширования."""
        user = cls.__new__(cls)
        user._user_id = data["user_id"]
        user._username = data["username"]
        user._hashed_password = data["hashed_password"]  
        user._salt = data["salt"]  
        user._registration_date = datetime.fromisoformat(data["registration_date"])
        return user


class Wallet:
    """Кошелёк для одной валюты."""

    def __init__(self, currency_code: str, balance: float = 0.0):
        self._currency = get_currency(currency_code)  # Валидация через реестр
        self._balance = 0.0
        self.balance = balance

    @property
    def currency_code(self) -> str:
        return self._currency.code

    @property
    def currency(self) -> Currency:
        return self._currency

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float):
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = float(value)

    def deposit(self, amount: float) -> None:
        """Пополнение баланса."""
        if amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")
        self._balance += amount

    def withdraw(self, amount: float) -> None:
        """Снятие средств с проверкой баланса."""
        if amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")
        if amount > self._balance:
            raise InsufficientFundsError(
                currency_code=self.currency_code, available=self._balance, required=amount
            )
        self._balance -= amount

    def get_balance_info(self) -> dict:
        """Информация о балансе."""
        return {
            "currency_code": self.currency_code,
            "balance": self._balance,
            "currency_info": self.currency.get_display_info(),
        }

    def to_dict(self) -> dict:
        """Сериализация."""
        return {"currency_code": self.currency_code, "balance": self._balance}

    @classmethod
    def from_dict(cls, data: dict) -> "Wallet":
        """Десериализация."""
        return cls(currency_code=data["currency_code"], balance=data["balance"])


class Portfolio:
    """Портфель пользователя со всеми кошельками."""

    def __init__(self, user_id: int, wallets: Optional[dict[str, Wallet]] = None):
        self._user_id = user_id
        self._wallets: dict[str, Wallet] = wallets or {}

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def wallets(self) -> dict[str, Wallet]:
        """Возвращает копию словаря кошельков."""
        return self._wallets.copy()

    def add_currency(self, currency_code: str) -> Wallet:
        """Добавление нового кошелька для валюты."""
        currency_code = currency_code.upper()
        if not currency_code:
            raise ValueError("Код валюты не может быть пустым")

        if currency_code in self._wallets:
            return self._wallets[currency_code]

        new_wallet = Wallet(currency_code)
        self._wallets[currency_code] = new_wallet
        return new_wallet

    def get_wallet(self, currency_code: str) -> Wallet:
        """Получение кошелька по коду валюты."""
        currency_code = currency_code.upper()
        if currency_code not in self._wallets:
            raise WalletNotFoundError(currency_code)
        return self._wallets[currency_code]

    def get_total_value(self, base_currency: str = "USD", exchange_rates: Optional[dict] = None) -> float:
        if exchange_rates is None:
            exchange_rates = db.get_exchange_rates().get("pairs", {})
        
        base_currency = base_currency.upper()
        total = 0.0
        
        for wallet in self._wallets.values():
            if wallet.currency_code == base_currency:
                total += wallet.balance
            else:
                pair = f"{wallet.currency_code}_{base_currency}"
                if pair in exchange_rates and "rate" in exchange_rates[pair]:
                    rate = exchange_rates[pair]["rate"]
                else:
                    # Попытка обратного курса
                    reverse_pair = f"{base_currency}_{wallet.currency_code}"
                    if reverse_pair in exchange_rates and "rate" in exchange_rates[reverse_pair]:
                        rate = 1.0 / exchange_rates[reverse_pair]["rate"]
                    else:
                        # Пропускаем валюту без курса (не ломаем расчёт всего портфеля)
                        continue
                total += wallet.balance * rate
        
        return total
    
    def to_dict(self) -> dict:
        """Сериализация портфеля."""
        return {
            "user_id": self._user_id,
            "wallets": {code: wallet.to_dict() for code, wallet in self._wallets.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Portfolio":
        """Десериализация портфеля."""
        wallets = {
            code: Wallet.from_dict(wallet_data)
            for code, wallet_data in data.get("wallets", {}).items()
        }
        return cls(user_id=data["user_id"], wallets=wallets)
