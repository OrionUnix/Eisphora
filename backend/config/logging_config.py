import os
import logging
import logging.config
from pathlib import Path


def setup_logging(base_dir: Path, debug: bool = False):
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "{levelname} {asctime} {module} {message}",
                "style": "{",
            },
        },
        "handlers": {
            "file_info": {
                "level": "INFO",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(logs_dir / "django_info.log"),
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 5,
                "formatter": "verbose",
            },
            "file_error": {
                "level": "ERROR",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(logs_dir / "django_errors.log"),
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 5,
                "formatter": "verbose",
            },
        },
        "loggers": {
            "django": {
                "handlers": ["file_info", "file_error"],
                "level": "INFO" if debug else "ERROR",
                "propagate": True,
            },
            # Exemple de logger applicatif
            "eisphora": {
                "handlers": ["file_info", "file_error"],
                "level": "DEBUG" if debug else "INFO",
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(logging_config)
