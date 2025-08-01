# -*- coding: utf-8 -*-

import os

import json
import logging
from typing import Any, Optional, Dict

_DEFAULT_FMT = "%(asctime)s %(levelname)s %(message)s"
_DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S"
_DEFAULT_LEVEL = "INFO"
_DEFAULT_STREAM = "stdout"
_DEFAULT_FILE_ENABLED = False
_DEFAULT_FILE_PATH = "logs/app.log"


def _to_line(data: Any) -> str:
    if isinstance(data, (dict, list)):
        return json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return str(data)


class AsyncLogger:
    def __init__(self, logger: logging.Logger):
        self._logger = logger
    async def debug(self, data: Any):    self._logger.debug(_to_line(data))
    async def info(self, data: Any):     self._logger.info(_to_line(data))
    async def warning(self, data: Any):  self._logger.warning(_to_line(data))
    async def error(self, data: Any):    self._logger.error(_to_line(data))
    async def critical(self, data: Any): self._logger.critical(_to_line(data))


_logger: Optional[AsyncLogger] = None


def _lg(cfg: Optional[Dict]) -> Dict:
    return (cfg or {}).get("logging") or {}


def _get(cfg: Optional[Dict], key: str, default):
    return _lg(cfg).get(key, default)


def get_logger() -> AsyncLogger:
    global _logger
    if _logger is None:
        _logger = AsyncLogger(logging.getLogger("app"))
    return _logger


def build_log_config(cfg: Optional[Dict] = None) -> Dict:
    level = str(_get(cfg, "level", _DEFAULT_LEVEL)).upper()
    fmt = _get(cfg, "format", _DEFAULT_FMT)
    datefmt = _get(cfg, "datefmt", _DEFAULT_DATEFMT)
    stream = _get(cfg, "stream", _DEFAULT_STREAM)
    file_enabled = bool(_get(cfg, "file", _DEFAULT_FILE_ENABLED))
    file_path = _get(cfg, "file_path", _DEFAULT_FILE_PATH)

    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "level": level,
            "formatter": "standard",
            "stream": "ext://sys.stdout" if str(stream).lower() == "stdout" else "ext://sys.stderr",
        }
    }
    if file_enabled:
        os.makedirs(os.path.dirname(os.path.abspath(file_path)) or ".", exist_ok=True)
        handlers["file"] = {
            "class": "logging.FileHandler",
            "level": level,
            "formatter": "standard",
            "filename": file_path,
            "encoding": "utf-8",
        }

    use_handlers = ["console"] + (["file"] if file_enabled else [])

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": fmt,
                "datefmt": datefmt,
            }
        },
        "handlers": handlers,
        "loggers": {
            "uvicorn.error": {
                "level": level,
                "handlers": use_handlers,
                "propagate": False,
            },
            "uvicorn.access": {
                "level": level,
                "handlers": use_handlers,
                "propagate": False,
            },
            "app": {
                "level": level,
                "handlers": use_handlers,
                "propagate": False,
            },
        },
        "root": {
            "level": level,
            "handlers": use_handlers,
        },
    }
