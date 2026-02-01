from pathlib import Path
from typing import Any


class SettingsLoader:
    _instance = None
    _config: dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._load_defaults()

    def _load_defaults(self) -> None:
        self._config = {
            "data_dir": "data",
            "rates_ttl_seconds": 300,
            "default_base_currency": "USD",
            "log_file": "logs/actions.log",
            "log_level": "INFO",
            "supported_currencies": ["USD", "EUR", "RUB", "BTC", "ETH"]
        }

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._config[key] = value

    def reload(self) -> None:
        self._load_defaults()

    @property
    def data_dir(self) -> Path:
        return Path(self.get("data_dir", "data"))

    @property
    def rates_ttl_seconds(self) -> int:
        return int(self.get("rates_ttl_seconds", 300))

    @property
    def default_base_currency(self) -> str:
        return str(self.get("default_base_currency", "USD"))


settings = SettingsLoader()
