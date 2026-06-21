from __future__ import annotations

import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from typing import Any

_LOG_FORMAT_JSON = "json"
_LOG_FORMAT_TEXT = "text"


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        obj: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            obj["exc"] = self.formatException(record.exc_info)
        extra = getattr(record, "extra_fields", None)
        if extra:
            obj.update(extra)
        return json.dumps(obj, default=str, ensure_ascii=False)


class ExtraLogger:
    def __init__(self, logger: logging.Logger, extra: dict[str, Any] | None = None) -> None:
        self._logger = logger
        self._extra = extra or {}

    def _log(self, level: int, msg: str, *args: Any, **kwargs: Any) -> None:
        valid_keys = {"exc_info", "stack_info", "extra"}
        standard_kwargs: dict[str, Any] = {}
        structured_fields: dict[str, Any] = {}

        for k, v in kwargs.items():
            if k in valid_keys:
                standard_kwargs[k] = v
            else:
                structured_fields[k] = v

        extra = standard_kwargs.pop("extra", {})
        if isinstance(extra, dict):
            structured_fields.update(extra)
        structured_fields.update(self._extra)

        if structured_fields:
            standard_kwargs["extra"] = {"extra_fields": structured_fields}

        self._logger.log(level, msg, *args, **standard_kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.ERROR, msg, *args, **kwargs)

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.DEBUG, msg, *args, **kwargs)

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.ERROR, msg, *args, **kwargs, exc_info=True)

    def child(self, **extra: Any) -> ExtraLogger:
        merged = {**self._extra, **extra}
        return ExtraLogger(self._logger, merged)


def get_logger(name: str, **extra: Any) -> ExtraLogger:
    return ExtraLogger(logging.getLogger(name), extra)


def setup_logging(level: str = "INFO", fmt: str = "json") -> None:
    root = logging.getLogger()
    root.setLevel(level.upper())

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level.upper())

    if fmt == _LOG_FORMAT_JSON:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S%z",
            )
        )

    root.handlers.clear()
    root.addHandler(handler)

    for logger_name in ("aiogram", "sqlalchemy.engine", "alembic", "httpx"):
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    get_logger(__name__).info("Logging initialized", level=level.upper(), format=fmt)


def generate_request_id() -> str:
    return uuid.uuid4().hex[:12]
