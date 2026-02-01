"""Бизнес-логика приложения с логированием и обработкой исключений."""
from typing import Optional

from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.database import db

from .exceptions import (
    AuthenticationError,
    UserNotFoundError,
    ValidationError,
    WalletNotFoundError,
)
from .models import Portfolio, User
from .utils import (
    format_currency_amount,
    get_exchange_rate,
    validate_currency_code,
    validate_positive_amount,
)


class UseCases:
    """Контейнер бизнес-логики приложения."""

    def __init__(self):
        self._current_user: Optional[User] = None
        self._current_portfolio: Optional[Portfolio] = None

    def register(self, username: str, password: str) -> User:
        """Регистрация нового пользователя."""

        if not username or not username.strip():
            raise ValidationError("username", "не может быть пустым")
        if len(password) < 4:
            raise ValidationError("password", "должен быть не короче 4 символов")

        users = db.load_json("users.json", [])
        if any(u["username"] == username for u in users):
            raise ValidationError("username", f"Имя пользователя '{username}' уже занято")

        user_id = db.get_next_user_id()
        user = User(user_id=user_id, username=username, password=password)

        users.append(user.to_dict())
        db.save_json("users.json", users)


        portfolio = Portfolio(user_id=user_id)
        portfolios = db.load_json("portfolios.json", [])
        portfolios.append(portfolio.to_dict())
        db.save_json("portfolios.json", portfolios)

        return user

    @log_action("LOGIN")
    def login(self, username: str, password: str) -> User:
        """Аутентификация пользователя."""

        users = db.load_json("users.json", [])
        user_data = next((u for u in users if u["username"] == username), None)

        if not user_data:
            raise UserNotFoundError(username)

        user = User.from_dict(user_data)

        if not user.verify_password(password):
            raise AuthenticationError(username)

        portfolios = db.load_json("portfolios.json", [])
        portfolio_data = next((p for p in portfolios if p["user_id"] == user.user_id), None)

        if not portfolio_data:
            portfolio = Portfolio(user_id=user.user_id)
            portfolios.append(portfolio.to_dict())
            db.save_json("portfolios.json", portfolios)
        else:
            portfolio = Portfolio.from_dict(portfolio_data)

        self._current_user = user
        self._current_portfolio = portfolio

        return user

    def logout(self) -> None:
        """Выход из системы."""
        self._current_user = None
        self._current_portfolio = None

    @property
    def current_user(self) -> Optional[User]:
        return self._current_user

    @property
    def current_portfolio(self) -> Optional[Portfolio]:
        return self._current_portfolio

    def ensure_authenticated(self) -> User:
        """Проверка аутентификации."""
        if self._current_user is None:
            raise AuthenticationError("anonymous")
        return self._current_user

    @log_action("BUY")
    def buy(self, currency_code: str, amount: float) -> dict:
        """Покупка валюты."""
        user = self.ensure_authenticated()
        currency_code = validate_currency_code(currency_code)
        amount = validate_positive_amount(amount, "amount")


        rates = db.get_exchange_rates()
        rate = get_exchange_rate(currency_code, "USD", rates)


        portfolio = self._current_portfolio
        if portfolio is None:
            raise RuntimeError("Портфель не загружен")

        wallet = portfolio.get_wallet(currency_code)
        wallet.deposit(amount)


        portfolios = db.load_json("portfolios.json", [])
        for p in portfolios:
            if p["user_id"] == user.user_id:
                p.update(portfolio.to_dict())
                break
        db.save_json("portfolios.json", portfolios)

        usd_value = amount * rate

        return {
            "success": True,
            "currency": currency_code,
            "amount": amount,
            "rate": rate,
            "usd_value": usd_value,
            "wallet_balance": wallet.balance
        }

    @log_action("SELL")
    def sell(self, currency_code: str, amount: float) -> dict:
        """Продажа валюты."""
        user = self.ensure_authenticated()
        currency_code = validate_currency_code(currency_code)
        amount = validate_positive_amount(amount, "amount")

        if self._current_portfolio is None:
            raise RuntimeError("Портфель не загружен")

        try:
            wallet = self._current_portfolio.get_wallet(currency_code)
        except WalletNotFoundError:
            raise WalletNotFoundError(currency_code) from None


        wallet.withdraw(amount)

        rates = db.get_exchange_rates()
        rate = get_exchange_rate(currency_code, "USD", rates)
        usd_revenue = amount * rate

        if currency_code != "USD":
            usd_wallet = self._current_portfolio.add_currency("USD")
            usd_wallet.deposit(usd_revenue)

        portfolios = db.load_json("portfolios.json", [])
        for p in portfolios:
            if p["user_id"] == user.user_id:
                p.update(self._current_portfolio.to_dict())
                break
        db.save_json("portfolios.json", portfolios)

        return {
            "success": True,
            "currency": currency_code,
            "amount": amount,
            "rate": rate,
            "usd_revenue": usd_revenue,
            "wallet_balance": wallet.balance
        }

    def show_portfolio(self, base_currency: str = "USD") -> dict:
        """Отображение портфеля."""
        user = self.ensure_authenticated()
        base_currency = validate_currency_code(base_currency)

        if self._current_portfolio is None:
            raise RuntimeError("Портфель не загружен")

        rates = db.get_exchange_rates()

        wallets_data = []
        total_value = 0.0

        for code, wallet in self._current_portfolio.wallets.items():
            if code == base_currency:
                value_in_base = wallet.balance
                rate = 1.0
            else:
                try:
                    rate = get_exchange_rate(code, base_currency, rates)
                    value_in_base = wallet.balance * rate
                except ValueError:
                    rate = 0.0
                    value_in_base = 0.0

            wallets_data.append({
                "currency": code,
                "balance": wallet.balance,
                "value_in_base": value_in_base,
                "rate": rate,
                "formatted_balance": format_currency_amount(wallet.balance, code),
                "formatted_value": format_currency_amount(value_in_base, base_currency)
            })
            total_value += value_in_base

        return {
            "username": user.username,
            "base_currency": base_currency,
            "wallets": wallets_data,
            "total_value": total_value,
            "formatted_total": format_currency_amount(total_value, base_currency)
        }

    def get_rate(self, from_code: str, to_code: str) -> dict:
        """Получение курса обмена."""
        from_code = validate_currency_code(from_code)
        to_code = validate_currency_code(to_code)

        rates = db.get_exchange_rates()
        rate = get_exchange_rate(from_code, to_code, rates)

        reverse_rate = 1.0 / rate if rate != 0 else 0.0

        return {
            "from": from_code,
            "to": to_code,
            "rate": rate,
            "reverse_rate": reverse_rate,
            "formatted_rate": f"{rate:.8f}",
            "formatted_reverse": f"{reverse_rate:.8f}",
            "updated_at": rates.get("last_refresh", "unknown")
        }
