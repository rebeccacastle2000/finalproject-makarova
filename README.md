# ValutaTrade Hub — Валютный кошелёк

Консольное приложение для управления портфелем фиатных и криптовалют с интеграцией реальных рыночных курсов. Система состоит из двух взаимодействующих компонентов: Core Service (управление пользователями и портфелями) и Parser Service (получение и кэширование курсов валют).

## Архитектура проекта

Проект реализован как полноценный Python-пакет с чётким разделением ответственности:

- **Core Service** — бизнес-логика управления пользователями, кошельками и транзакциями
- **Parser Service** — фоновый сбор актуальных курсов из внешних источников
- **CLI** — единая точка входа для пользователя с интуитивным интерфейсом

Данные хранятся в JSON-файлах, что обеспечивает простоту развёртывания и отладки без необходимости внешней СУБД.

## Структура каталогов
finalproject_makarova/
├── data/
│ ├── users.json # Регистрация пользователей 
│ ├── portfolios.json # Портфели и кошельки пользователей
│ ├── rates.json # Кэш актуальных курсов для быстрого доступа
│ └── exchange_rates.json # История всех замеров курсов с метаданными
├── valutatrade_hub/
│ ├── core/
│ │ ├── models.py # Модели данных (User, Wallet, Portfolio)
│ │ ├── currencies.py # Иерархия валют (FiatCurrency, CryptoCurrency)
│ │ ├── exceptions.py # Доменные исключения
│ │ ├── usecases.py # Бизнес-логика операций
│ │ └── utils.py # Валидация и утилиты конвертации
│ ├── infra/
│ │ ├── settings.py # Singleton SettingsLoader
│ │ └── database.py # Singleton DatabaseManager (работа с JSON)
│ ├── parser_service/
│ │ ├── config.py # Конфигурация API и параметров обновления
│ │ ├── api_clients.py # Клиенты CoinGecko и ExchangeRate-API
│ │ ├── updater.py # Координация обновления курсов
│ │ ├── storage.py # Управление кэшем и историей
│ │ └── scheduler.py # Планировщик периодического обновления
│ ├── cli/
│ │ └── interface.py # Командный интерфейс пользователя
│ ├── logging_config.py # Настройка логирования с ротацией
│ └── decorators.py # Декоратор @log_action для аудита операций
├── main.py # Точка входа приложения
├── Makefile # Автоматизация рутинных операций
├── pyproject.toml # Конфигурация Poetry и метаданные пакета
├── .gitignore # Исключение временных файлов и секретов
└── README.md # Документация проекта

## Требования

- Python 3.9 или новее
- Poetry для управления зависимостями
- Доступ в интернет для работы Parser Service

## Установка

1. Клонирование репозитория:

```bash
git clone https://github.com/rebeccacastle2000/finalproject-makarova.git
cd finalproject_makarova
```

2. Установка зависимостей через Makefile:
```bash
make install
```

3. Настройка API-ключа для ExchangeRate-API:
Создайте файл .env в корне проекта:
```bash
echo "EXCHANGERATE_API_KEY=ваш_ключ_здесь" > .env
```

## Запуск приложения
```bash
make project
```

## Примеры использования команд CLI

### Сценарий 1: Полный цикл работы с новым пользователем (ответы на операции без учета INFO)

valutatrade> help

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

valutatrade> register --username test2 --password Trade1234!
✅ Пользователь 'test2' зарегистрирован (id=5)
   Теперь выполните вход: login --username <имя> --password <пароль>

valutatrade> login --username test2 --password Trade1234!
✅ Вы вошли как 'test2'

valutatrade> show-portfolio
Портфель пользователя 'test2' (база: USD):
------------------------------------------------------------
  USD    : 10000.00        → 10000.00        USD
------------------------------------------------------------
  ИТОГО: 10000.00                            USD

valutatrade> buy --currency BTC --amount 0.05
✅ Покупка выполнена: 0.050000 BTC по курсу 76929.0000 BTC/USD
   Стоимость покупки: 3,846.45 USD
   Новый баланс BTC: 0.050000
   Оценочная стоимость: 3,846.45 USD

valutatrade> buy --currency EUR --amount 200
✅ Покупка выполнена: 200.000000 EUR по курсу 1.1895 EUR/USD
   Стоимость покупки: 237.90 USD
   Новый баланс EUR: 200.000000
   Оценочная стоимость: 237.90 USD


valutatrade> sell --currency BTC --amount 0.02
✅ Продажа выполнена: 0.020000 BTC по курсу 76929.0000 BTC/USD
   Зачислено на USD: 1,538.58 USD
   Новый баланс BTC: 0.030000
   Выручка: 1,538.58 USD

valutatrade> logout
✅ Вы вышли из системы

valutatrade> exit
До свидания!

###Сценарий 2: Работа с курсами валют и обновление данных

valutatrade> help

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

valutatrade> login --username test --password 1234
✅ Вы вошли как 'test'

valutatrade> buy --currency EUR --amount 5
✅ Покупка выполнена: 5.000000 EUR по курсу 1.1895 EUR/USD
   Стоимость покупки: 5.95 USD
   Новый баланс EUR: 15.000000
   Оценочная стоимость: 5.95 USD

valutatrade> get-rate --from USD --to EUR

Курс USD→EUR: 0.84070000
Обратный курс EUR→USD: 1.18948495
Обновлено: 2026-02-01T19:56:06.838583+00:00

valutatrade> sell --currency EUR --amount 5
✅ Продажа выполнена: 5.000000 EUR по курсу 1.1895 EUR/USD
   Зачислено на USD: 5.95 USD
   Новый баланс EUR: 10.000000
   Выручка: 5.95 USD

Сценарий 3: Обработка ошибок и валидация входных данных
valutatrade> register --username trader_john --password Trade123!
❌ Ошибка регистрации: Ошибка валидации поля 'username': Имя пользователя 'trader_john' уже занято

valutatrade> register --username new_user --password 123
❌ Ошибка регистрации: Ошибка валидации поля 'password': должен быть не короче 4 символов

valutatrade> login --username unknown_user --password wrongpass
❌ Ошибка входа: Пользователь 'unknown_user' не найден

valutatrade> login --username trader_john --password wrongpass
❌ Ошибка входа: Неверный пароль для пользователя 'trader_john'

valutatrade> buy --currency INVALID --amount 100
❌ Ошибка покупки: Ошибка валидации поля 'currency_code': Неизвестная валюта 'INVALID'

valutatrade> buy --currency BTC --amount -0.01
❌ Ошибка покупки: Ошибка валидации поля 'amount': должен быть положительным числом

valutatrade> buy --currency BTC --amount abc
❌ Ошибка: 'amount' должен быть числом

valutatrade> sell --currency BTC --amount 100
❌ Недостаточно средств: доступно 0.030000 BTC, требуется 100.000000 BTC

valutatrade> sell --currency BTC --amount 100
❌ Ошибка продажи: У вас нет кошелька 'BTC'. Добавьте валюту: она создаётся автоматически при первой покупке.

valutatrade> get-rate --from INVALID --to USD
❌ Ошибка получения курса: Ошибка валидации поля 'currency_code': Неизвестная валюта 'INVALID'


