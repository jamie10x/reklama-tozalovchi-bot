import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    root.setLevel(level.upper())

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level.upper())

    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    handler.setFormatter(fmt)

    root.handlers.clear()
    root.addHandler(handler)

    for logger_name in ("aiogram", "sqlalchemy.engine", "alembic"):
        logging.getLogger(logger_name).setLevel(logging.WARNING)
