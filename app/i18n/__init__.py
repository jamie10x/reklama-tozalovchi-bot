from __future__ import annotations

from typing import Any

from app.i18n.uz import UZ


class I18n:
    def __init__(self, locale: str = "uz") -> None:
        self.locale = locale
        self._translations = self._load()

    def _load(self) -> dict[str, Any]:
        if self.locale == "uz":
            return UZ
        return UZ

    def t(self, key: str, default: str | None = None, **kwargs: Any) -> str:
        parts = key.split(".")
        val: Any = self._translations
        for part in parts:
            if isinstance(val, dict):
                val = val.get(part)
                if val is None:
                    return default if default is not None else key
            else:
                return default if default is not None else key
        if isinstance(val, str):
            return val.format(**kwargs) if kwargs else val
        return default if default is not None else key

    def has_key(self, key: str) -> bool:
        return self.t(key) != key
