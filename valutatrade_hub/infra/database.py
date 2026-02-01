import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from .settings import settings


class DatabaseManager:
    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._data_dir = settings.data_dir
        self._data_dir.mkdir(exist_ok=True)

    def _get_path(self, filename: str) -> Path:
        return self._data_dir / filename

    def load_json(self, filename: str, default: Any = None) -> Any:
        path = self._get_path(filename)
        with self._lock:
            if not path.exists():
                return default if default is not None else []

            try:
                with open(path, encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return default if default is not None else []

    def save_json(self, filename: str, data: Any) -> None:
        path = self._get_path(filename)
        with self._lock, open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_next_user_id(self) -> int:
        users = self.load_json("users.json", [])
        if not users:
            return 1
        return max(user["user_id"] for user in users) + 1

    def get_exchange_rates(self) -> dict[str, Any]:
        return self.load_json("rates.json", self._get_default_rates())

    def update_exchange_rates(self, rates: dict[str, Any]) -> None:
        rates["last_refresh"] = datetime.now().isoformat()
        rates["source"] = "ParserServiceStub"
        self.save_json("rates.json", rates)

    def _get_default_rates(self) -> dict[str, Any]:
        now = datetime.now().isoformat()
        return {
            "EUR_USD": {"rate": 1.0786, "updated_at": now},
            "BTC_USD": {"rate": 59337.21, "updated_at": now},
            "RUB_USD": {"rate": 0.01016, "updated_at": now},
            "ETH_USD": {"rate": 3720.00, "updated_at": now},
            "SOL_USD": {"rate": 145.50, "updated_at": now},
            "XRP_USD": {"rate": 0.58, "updated_at": now},
            "GBP_USD": {"rate": 1.27, "updated_at": now},
            "JPY_USD": {"rate": 0.0067, "updated_at": now},
            "source": "StubService",
            "last_refresh": now,
        }


db = DatabaseManager()
