import json
from pathlib import Path
from typing import Any


class DataStorage:
    """Управление JSON-хранилищем данных."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

    def _get_path(self, filename: str) -> Path:
        return self.data_dir / filename

    def load_json(self, filename: str, default: Any = None) -> Any:
        """Загрузка данных из JSON файла."""
        path = self._get_path(filename)
        if not path.exists():
            return default if default is not None else []

        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return default if default is not None else []

    def save_json(self, filename: str, data: Any) -> None:
        """Сохранение данных в JSON файл."""
        path = self._get_path(filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_next_user_id(self) -> int:
        """Генерация следующего уникального user_id."""
        users = self.load_json("users.json", [])
        if not users:
            return 1
        return max(user["user_id"] for user in users) + 1
