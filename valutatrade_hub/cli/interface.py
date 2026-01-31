import shlex
from typing import Optional

from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.core.utils import DataStorage


class CLI:
    """Консольный интерфейс приложения."""

    def __init__(self):
        self.storage = DataStorage()
        self.current_user: Optional[User] = None
        self.current_portfolio: Optional[Portfolio] = None
        self._init_data_files()

    def _init_data_files(self):
        """Инициализация пустых JSON файлов при первом запуске."""
        if not self.storage._get_path("users.json").exists():
            self.storage.save_json("users.json", [])
        if not self.storage._get_path("portfolios.json").exists():
            self.storage.save_json("portfolios.json", [])
        if not self.storage._get_path("rates.json").exists():
            # Инициализация заглушек для курсов
            self.storage.save_json(
                "rates.json",
                {
                    "EUR_USD": {"rate": 1.0786, "updated_at": "2025-10-09T10:30:00"},
                    "BTC_USD": {"rate": 59337.21, "updated_at": "2025-10-09T10:29:42"},
                    "RUB_USD": {"rate": 0.01016, "updated_at": "2025-10-09T10:31:12"},
                    "ETH_USD": {"rate": 3720.00, "updated_at": "2025-10-09T10:35:00"},
                    "source": "StubService",
                    "last_refresh": "2025-10-09T10:35:00",
                },
            )

    def run(self):
        """Основной цикл CLI."""
        print("Добро пожаловать в ValutaTrade Hub! (v0.1.0)")
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
            except Exception as e:
                print(f"❌ Ошибка: {e}")

    def _show_help(self):
        """Вывод справки по командам."""
        help_text = """
Доступные команды:
  register --username <имя> --password <пароль>  - Регистрация нового пользователя
  login --username <имя> --password <пароль>     - Вход в систему
  show-portfolio [--base <валюта>]              - Показать портфель (по умолчанию USD)
  buy --currency <код> --amount <сумма>         - Покупка валюты
  sell --currency <код> --amount <сумма>        - Продажа валюты
  get-rate --from <валюта> --to <валюта>        - Текущий курс обмена
  exit                                          - Выход из приложения
        """
        print(help_text)

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

        if command == "register":
            self._cmd_register(args)
        elif command == "login":
            self._cmd_login(args)
        elif command == "show-portfolio":
            self._cmd_show_portfolio(args)
        elif command == "buy":
            self._cmd_buy(args)
        elif command == "sell":
            self._cmd_sell(args)
        elif command == "get-rate":
            self._cmd_get_rate(args)
        else:
            print(f"❌ Неизвестная команда: {command}")

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

    def _cmd_register(self, args: dict):
        print("⚠️  Команда register: реализация в процессе разработки")

    def _cmd_login(self, args: dict):
        print("⚠️  Команда login: реализация в процессе разработки")

    def _cmd_show_portfolio(self, args: dict):
        print("⚠️  Команда show-portfolio: реализация в процессе разработки")

    def _cmd_buy(self, args: dict):
        print("⚠️  Команда buy: реализация в процессе разработки")

    def _cmd_sell(self, args: dict):
        print("⚠️  Команда sell: реализация в процессе разработки")

    def _cmd_get_rate(self, args: dict):
        print("⚠️  Команда get-rate: реализация в процессе разработки")
