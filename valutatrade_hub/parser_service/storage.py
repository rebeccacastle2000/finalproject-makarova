"""Хранилище для курсов валют: кэш и исторические данные."""

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import config


class RatesStorage:
    """Управление хранением курсов валют."""

    def __init__(self):
        self.rates_path = Path(config.RATES_FILE_PATH)
        self.history_path = Path(config.HISTORY_FILE_PATH)
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Создание директорий для файлов данных при необходимости."""
        self.rates_path.parent.mkdir(parents=True, exist_ok=True)

    def load_current_rates(self) -> dict[str, Any]:
        """Загрузка текущих курсов из кэша (rates.json)."""
        if not self.rates_path.exists():
            return {"pairs": {}, "last_refresh": datetime.now(timezone.utc).isoformat()}

        try:
            with open(self.rates_path, encoding="utf-8") as f:
                data = json.load(f)
                if "pairs" not in data:
                    data["pairs"] = {}
                if "last_refresh" not in data:
                    data["last_refresh"] = datetime.now(timezone.utc).isoformat()
                return data
        except (json.JSONDecodeError, OSError):
            return {"pairs": {}, "last_refresh": datetime.now(timezone.utc).isoformat()}

    def save_current_rates(self, rates: dict[str, float], source: str = "ParserService") -> None:
        """Сохранение текущих курсов в кэш (rates.json) с атомарной записью."""
        current_data = self.load_current_rates()
        now = datetime.now(timezone.utc).isoformat()

        for pair, rate in rates.items():
            current_data["pairs"][pair] = {"rate": rate, "updated_at": now, "source": source}

        current_data["last_refresh"] = now

        self._atomic_write(self.rates_path, current_data)

    def append_to_history(self, pair: str, rate: float, source: str) -> None:
        """Добавление записи в историю обменных курсов."""
        if not pair or "_" not in pair:
            raise ValueError(f"Некорректный формат пары валют: {pair}")

        now = datetime.now(timezone.utc).isoformat()
        parts = pair.split("_")
        from_currency = parts[0].upper()
        to_currency = parts[1].upper() if len(parts) > 1 else config.BASE_CURRENCY

        record = {
            "id": f"{from_currency}_{to_currency}_{now.replace(':', '').replace('-', '').replace('.', '').replace('+', '')}",
            "from_currency": from_currency,
            "to_currency": to_currency,
            "rate": rate,
            "timestamp": now,
            "source": source,
            "meta": {"request_ms": 0, "status_code": 200},
        }

        history = self._load_history()
        history.append(record)
        self._atomic_write(self.history_path, history)

    def _load_history(self) -> list[dict[str, Any]]:
        """Загрузка истории курсов."""
        if not self.history_path.exists():
            return []

        try:
            with open(self.history_path, encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _atomic_write(self, path: Path, data: Any) -> None:
        """Атомарная запись данных в файл (через временный файл)."""
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
        ) as tmp_file:
            json.dump(data, tmp_file, ensure_ascii=False, indent=2)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())

        os.replace(tmp_file.name, path)
