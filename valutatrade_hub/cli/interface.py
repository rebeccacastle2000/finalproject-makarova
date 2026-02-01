"""Консольный интерфейс приложения с обработкой ошибок."""

import shlex
import sys
try:
    import readline  # ← ЭТА СТРОКА РЕШАЕТ ПРОБЛЕМУ СО СТРЕЛКАМИ
except ImportError:
    pass  # Windows — работаем без истории команд (но проект ориентирован на Unix)


from prettytable import PrettyTable

from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    AuthenticationError,
    CurrencyNotFoundError,
    InsufficientFundsError,
    UserNotFoundError,
    ValidationError,
    WalletNotFoundError,
)
from valutatrade_hub.core.usecases import UseCases
from valutatrade_hub.infra.database import db
from valutatrade_hub.logging_config import setup_logging
from valutatrade_hub.parser_service.storage import RatesStorage
from valutatrade_hub.parser_service.updater import RatesUpdater


class CLI:
    """Консольный интерфейс приложения."""

    def __init__(self):
        setup_logging()
        self.use_cases = UseCases()
        self._init_data_files()

    def _init_data_files(self):
        _ = db.get_exchange_rates()

    def run(self):
        """Основной цикл CLI."""
        print("Добро пожаловать в ValutaTrade Hub! (v0.2.0)")
        print("Введите 'help' для списка команд или 'exit' для выхода.\n")

        while True:
            try:
                cmd_input = input("valutatrade> ").strip()
                if not cmd_input:
                    continue

                if cmd_input.lower() in ("exit", "quit"):
                    print("До свидания!")
                    break

                if cmd_input.lower() == "help":
                    self._show_help()
                    continue

                self._process_command(cmd_input)

            except KeyboardInterrupt:
                print("\n\nПринудительный выход. До свидания!")
                break
            except EOFError:
                print("\nДо свидания!")
                break
            except Exception as e:
                # Обработка неожиданных ошибок
                print(f"❌ Критическая ошибка: {type(e).__name__}: {e}")
                import logging

                logging.getLogger("actions").exception("Unhandled exception in CLI")

    def _show_help(self):
        """Вывод справки по командам."""
        help_text = """
Доступные команды:
  register --username <имя> --password <пароль>  - Регистрация нового пользователя
  login --username <имя> --password <пароль>     - Вход в систему
  logout                                        - Выход из системы
  show-portfolio [--base <валюта>]              - Показать портфель (по умолчанию USD)
  buy --currency <код> --amount <сумма>         - Покупка валюты
  sell --currency <код> --amount <сумма>        - Продажа валюты
  get-rate --from <валюта> --to <валюта>        - Текущий курс обмена
  exit                                          - Выход из приложения

Поддерживаемые валюты: USD, EUR, RUB, GBP, JPY, BTC, ETH, SOL, XRP
        """
        print(help_text)

    def _parse_args(self, arg_list: list) -> dict:
        """Парсинг аргументов вида --key value."""
        args = {}
        i = 0
        while i < len(arg_list):
            if arg_list[i].startswith("--"):
                key = arg_list[i][2:]
                if i + 1 < len(arg_list) and not arg_list[i + 1].startswith("--"):
                    args[key] = arg_list[i + 1]
                    i += 2
                else:
                    args[key] = True
                    i += 1
            else:
                i += 1
        return args

    def _process_command(self, cmd_input: str):
        """Парсинг и выполнение команды."""
        try:
            parts = shlex.split(cmd_input)
        except ValueError as e:
            print(f"❌ Ошибка парсинга команды: {e}")
            return

        if not parts:
            return

        command = parts[0].lower()
        args = self._parse_args(parts[1:])

        # Диспетчеризация команд
        try:
            if command == "register":
                self._cmd_register(args)
            elif command == "login":
                self._cmd_login(args)
            elif command == "logout":
                self._cmd_logout()
            elif command == "show-portfolio":
                self._cmd_show_portfolio(args)
            elif command == "buy":
                self._cmd_buy(args)
            elif command == "sell":
                self._cmd_sell(args)
            elif command == "get-rate":
                self._cmd_get_rate(args)
            elif command == "update-rates":
                self._cmd_update_rates(args)
            elif command == "show-rates":
                self._cmd_show_rates(args)
            else:
                print(f"❌ Неизвестная команда: {command}. Введите 'help' для справки.")
        except (UserNotFoundError, AuthenticationError) as e:
            print(f"❌ Аутентификация: {e}")
        except CurrencyNotFoundError as e:
            print(f"❌ Валюта: {e}")
            print("   Поддерживаемые валюты: USD, EUR, RUB, BTC, ETH, SOL, XRP, GBP, JPY")
        except InsufficientFundsError as e:
            print(f"❌ Недостаточно средств: {e}")
        except WalletNotFoundError as e:
            print(f"❌ Кошелёк: {e}")
        except ValidationError as e:
            print(f"❌ Валидация: {e}")
        except ApiRequestError as e:
            print(f"❌ API: {e}")
            print("   Повторите попытку позже или проверьте подключение к сети.")
        except Exception as e:
            print(f"❌ Ошибка выполнения команды: {type(e).__name__}: {e}")

    def _cmd_register(self, args: dict):
        username = args.get("username")
        password = args.get("password")

        if not username or not password:
            print("❌ Требуются аргументы: --username <имя> --password <пароль>")
            return

        try:
            user = self.use_cases.register(username, password)
            print(f"✅ Пользователь '{user.username}' зарегистрирован (id={user.user_id})")
            print("   Теперь выполните вход: login --username <имя> --password <пароль>")
        except ValidationError as e:
            print(f"❌ Ошибка регистрации: {e}")

    def _cmd_login(self, args: dict):
        username = args.get("username")
        password = args.get("password")

        if not username or not password:
            print("❌ Требуются аргументы: --username <имя> --password <пароль>")
            return

        try:
            user = self.use_cases.login(username, password)
            print(f"✅ Вы вошли как '{user.username}'")
        except (UserNotFoundError, AuthenticationError) as e:
            print(f"❌ Ошибка входа: {e}")

    def _cmd_logout(self):
        self.use_cases.logout()
        print("✅ Вы вышли из системы")

    def _cmd_show_portfolio(self, args: dict):
        if self.use_cases.current_user is None:
            print("❌ Сначала выполните вход: login --username <имя> --password <пароль>")
            return

        base_currency = args.get("base", "USD")

        try:
            portfolio = self.use_cases.show_portfolio(base_currency)

            print(f"\nПортфель пользователя '{portfolio['username']}' (база: {base_currency}):")
            print("-" * 60)

            if not portfolio["wallets"]:
                print("   У вас пока нет кошельков. Купите первую валюту!")
            else:
                for w in portfolio["wallets"]:
                    print(
                        f"  {w['currency']:6} : {w['formatted_balance']:15} "
                        f"→ {w['formatted_value']:15} {base_currency}"
                    )
                print("-" * 60)
                print(f"  ИТОГО: {portfolio['formatted_total']:35} {base_currency}")
            print()
        except Exception as e:
            print(f"❌ Ошибка отображения портфеля: {e}")

    def _cmd_buy(self, args: dict):
        if self.use_cases.current_user is None:
            print("❌ Сначала выполните вход: login --username <имя> --password <пароль>")
            return

        currency = args.get("currency")
        amount = args.get("amount")

        if not currency or not amount:
            print("❌ Требуются аргументы: --currency <код> --amount <сумма>")
            return

        try:
            amount = float(amount)
            result = self.use_cases.buy(currency, amount)

            print(f"✅ Покупка выполнена: {result['amount']:.6f} {result['currency']} "
                f"по курсу {result['rate']:.4f} {result['currency']}/USD")
            print(f"   Стоимость покупки: {result['usd_value']:,.2f} USD")
            print(f"   Новый баланс {result['currency']}: {result['wallet_balance']:.6f}")
            print(f"   Оценочная стоимость: {result['usd_value']:,.2f} USD\n")
        except ValueError:
            print("❌ Ошибка: 'amount' должен быть числом")
        except Exception as e:
            print(f"❌ Ошибка покупки: {e}")

    def _cmd_sell(self, args: dict):
        if self.use_cases.current_user is None:
            print("❌ Сначала выполните вход: login --username <имя> --password <пароль>")
            return

        currency = args.get("currency")
        amount = args.get("amount")

        if not currency or not amount:
            print("❌ Требуются аргументы: --currency <код> --amount <сумма>")
            return

        try:
            amount = float(amount)
            result = self.use_cases.sell(currency, amount)

            print(f"✅ Продажа выполнена: {result['amount']:.6f} {result['currency']} "
                f"по курсу {result['rate']:.4f} {result['currency']}/USD")
            print(f"   Зачислено на USD: {result['usd_revenue']:,.2f} USD")
            print(f"   Новый баланс {result['currency']}: {result['wallet_balance']:.6f}")
            print(f"   Выручка: {result['usd_revenue']:,.2f} USD\n")
        except ValueError:
            print("❌ Ошибка: 'amount' должен быть числом")
        except Exception as e:
            print(f"❌ Ошибка продажи: {e}")

    def _cmd_get_rate(self, args: dict):
        from_code = args.get("from")
        to_code = args.get("to")

        if not from_code or not to_code:
            print("❌ Требуются аргументы: --from <валюта> --to <валюта>")
            return

        try:
            rate_info = self.use_cases.get_rate(from_code, to_code)

            print(f"\nКурс {rate_info['from']}→{rate_info['to']}: {rate_info['formatted_rate']}")
            print(
                f"Обратный курс {rate_info['to']}→{rate_info['from']}: {rate_info['formatted_reverse']}"
            )
            print(f"Обновлено: {rate_info['updated_at']}\n")
        except Exception as e:
            print(f"❌ Ошибка получения курса: {e}")

    def _cmd_update_rates(self, args: dict):
        """Команда обновления курсов валют."""
        source = args.get("source")

        if source and source not in ("coingecko", "exchangerate"):
            print(f"❌ Неверный источник: {source}. Допустимые значения: coingecko, exchangerate")
            return

        try:
            updater = RatesUpdater()
            print("🔄 Запуск обновления курсов...")

            result = updater.run_update(source=source)

            if result["success"]:
                print(
                    f"✅ Обновление успешно завершено. Обновлено пар: {len(result['updated_pairs'])}"
                )
                print(f"   Последнее обновление: {result['timestamp']}")
            else:
                print("⚠️  Обновление завершено с ошибками:")
                for error in result["errors"]:
                    print(f"   • {error}")
                if result["updated_pairs"]:
                    print(f"   Успешно обновлено пар: {len(result['updated_pairs'])}")
                else:
                    print("   Ни одна пара не была обновлена")

        except Exception as e:
            print(f"❌ Ошибка при обновлении курсов: {e}")

    def _cmd_show_rates(self, args: dict):
        """Команда показа текущих курсов."""
        currency_filter = args.get("currency")
        top_n = args.get("top")

        try:
            storage = RatesStorage()
            rates_data = storage.load_current_rates()
            pairs = rates_data.get("pairs", {})

            if not pairs:
                print(
                    "ℹ️  Локальный кеш курсов пуст. Выполните 'update-rates', чтобы загрузить данные."
                )
                return

            # Фильтрация по валюте
            filtered_pairs = {}
            if currency_filter:
                currency_filter = currency_filter.upper()
                for pair, data in pairs.items():
                    if pair.startswith(f"{currency_filter}_") or pair.endswith(
                        f"_{currency_filter}"
                    ):
                        filtered_pairs[pair] = data
                if not filtered_pairs:
                    print(f"ℹ️  Курс для '{currency_filter}' не найден в кеше.")
                    return
            else:
                filtered_pairs = pairs

            # Сортировка для --top
            if top_n:
                try:
                    top_n = int(top_n)
                    sorted_pairs = sorted(
                        filtered_pairs.items(), key=lambda x: x[1]["rate"], reverse=True
                    )[:top_n]
                except ValueError:
                    print(f"❌ Неверное значение --top: {top_n}")
                    return
            else:
                # Сортировка по алфавиту
                sorted_pairs = sorted(filtered_pairs.items(), key=lambda x: x[0])

            # Формирование таблицы
            table = PrettyTable()
            table.field_names = ["Пара", "Курс", "Обновлено", "Источник"]
            table.align["Пара"] = "l"
            table.align["Курс"] = "r"
            table.align["Обновлено"] = "l"
            table.align["Источник"] = "l"

            for pair, data in sorted_pairs:
                rate = data["rate"]
                updated_at = data["updated_at"].replace("T", " ").split(".")[0]
                source = data["source"]

                # Форматирование курса в зависимости от типа валюты
                if pair.startswith("BTC") or pair.startswith("ETH") or pair.startswith("SOL"):
                    rate_str = f"{rate:,.2f}"
                else:
                    rate_str = f"{rate:.4f}"

                table.add_row([pair, rate_str, updated_at, source])

            last_refresh = rates_data.get("last_refresh", "unknown").replace("T", " ").split(".")[0]
            print(f"\nАктуальные курсы (последнее обновление: {last_refresh})")
            print(table)
            print()

        except Exception as e:
            print(f"❌ Ошибка при отображении курсов: {e}")
