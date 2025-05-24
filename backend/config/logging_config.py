import os
import logging.config
from pathlib import Path
from pythonjsonlogger import jsonlogger
from dotenv import load_dotenv, find_dotenv
from django.conf import settings 

# Charge .env uniquement s'il est présent
dotenv_path = find_dotenv()
if dotenv_path:
    load_dotenv(dotenv_path)
else:
    print("⚠️  Fichier .env non trouvé. Mode dev présumé.")

# Récupère une variable DEBUG_MODE du .env (True/False), ou False par défaut
debug_mode = os.getenv("DEBUG", "false").lower() == "true"


def setup_logging(base_dir: Path, debug: bool = False):
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    admin_email = os.getenv("ADMIN_EMAIL")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_host = os.getenv("SMTP_HOST", "smtp.example.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))

    enable_telegram = os.getenv("ENABLE_TELEGRAM", "false").lower() == "true"
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

    class TelegramHandler(logging.Handler):
        def emit(self, record):
            try:
                import requests
                log_entry = self.format(record)
                requests.post(
                    f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                    data={"chat_id": telegram_chat_id, "text": log_entry}
                )
            except Exception:
                self.handleError(record)

    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                '()': jsonlogger.JsonFormatter,
                'format': '%(levelname)s %(asctime)s %(module)s %(message)s'
            },
        },
        "handlers": {
            "file_info": {
                "level": "INFO",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": logs_dir / "info.json.log",
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 5,
                "formatter": "json",
            },
            "file_error": {
                "level": "ERROR",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": logs_dir / "errors.json.log",
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 5,
                "formatter": "json",
            },
        },
        "loggers": {
            "django": {
                "handlers": ["file_info", "file_error"],
                "level": "DEBUG" if debug else "ERROR",
                "propagate": True,
            },
            "eisphora": {
                "handlers": ["file_info", "file_error"],
                "level": "DEBUG" if debug else "INFO",
                "propagate": False,
            },
        },
    }

    if not debug_mode and admin_email:
        LOGGING["handlers"]["mail_admins"] = {
            "level": "ERROR",
            "class": "logging.handlers.SMTPHandler",
            "mailhost": (smtp_host, smtp_port),
            "fromaddr": admin_email,
            "toaddrs": [admin_email],
            "subject": "Django Error",
            "credentials": (smtp_user, smtp_password),
            "secure": (),
            "formatter": "json",
        }
        LOGGING["loggers"]["django"]["handlers"].append("mail_admins")

    if enable_telegram and telegram_token and telegram_chat_id:
        LOGGING["handlers"]["telegram"] = {
            "level": "ERROR",
            "class": "logging_config.TelegramHandler",
            "formatter": "json",
        }
        LOGGING["loggers"]["eisphora"]["handlers"].append("telegram")

    logging.config.dictConfig(LOGGING)

    if debug_mode:
        logging.getLogger("eisphora").info("🛠 Mode dev : logs débug activés.")
    elif enable_telegram:
        logging.getLogger("eisphora").info("📬 Telegram logging activé.")
