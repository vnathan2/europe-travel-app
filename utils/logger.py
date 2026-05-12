"""
utils/logger.py
Logger compartido para europe-travel-app.

Comportamiento:
- En Cloud Run (variable K_SERVICE presente): emite JSON estructurado a stdout.
  Cloud Logging parsea automáticamente los campos severity y message.
- En local: formato legible con timestamp.

Uso:
    from utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Iniciando ingesta ciudad=%s", ciudad)
    logger.warning("Fallback a env var para %s", key)
    logger.exception("Error procesando doc id=%s", doc_id)

Sin dependencias externas — solo logging y json de stdlib.
"""

import json
import logging
import os
import traceback


_IN_CLOUD_RUN = bool(os.getenv("K_SERVICE"))

# Nombre del logger raíz de la app. Todos los get_logger(__name__) con
# prefijo "modules." o "utils." heredan de este.
_APP_LOGGER = "europe_travel"


class _JsonFormatter(logging.Formatter):
    """
    Emite una línea JSON por registro, compatible con Cloud Logging.
    Campos estándar: severity, message, module, funcName, lineno.
    Si hay excepción, agrega exception con el traceback completo.
    """

    # Mapeo de niveles Python → severidad Cloud Logging
    _SEVERITY = {
        logging.DEBUG:    "DEBUG",
        logging.INFO:     "INFO",
        logging.WARNING:  "WARNING",
        logging.ERROR:    "ERROR",
        logging.CRITICAL: "CRITICAL",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "severity": self._SEVERITY.get(record.levelno, "DEFAULT"),
            "message":  record.getMessage(),
            "module":   record.module,
            "function": record.funcName,
            "line":     record.lineno,
        }
        if record.exc_info:
            payload["exception"] = "".join(
                traceback.format_exception(*record.exc_info)
            ).strip()
        return json.dumps(payload, ensure_ascii=False)


class _ReadableFormatter(logging.Formatter):
    """Formato legible para desarrollo local."""
    def __init__(self):
        super().__init__(
            fmt="%(asctime)s [%(levelname)-8s] %(name)s — %(message)s",
            datefmt="%H:%M:%S",
        )


def _build_handler() -> logging.Handler:
    handler = logging.StreamHandler()
    handler.setFormatter(
        _JsonFormatter() if _IN_CLOUD_RUN else _ReadableFormatter()
    )
    return handler


def _get_app_logger() -> logging.Logger:
    """
    Configura el logger raíz de la app una sola vez.
    Los loggers hijos heredan el handler vía propagación normal.
    No tocamos el logger root de Python para no interferir con Streamlit.
    """
    app_logger = logging.getLogger(_APP_LOGGER)

    if not app_logger.handlers:
        app_logger.addHandler(_build_handler())
        app_logger.setLevel(logging.INFO)
        # propagate=True (default): los mensajes suben al root de Python,
        # lo que permite que Streamlit siga capturando logs normalmente.
        # NO ponemos propagate=False aquí.

    return app_logger


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Retorna un logger configurado para el módulo indicado.

    Si name empieza con 'modules.' o 'utils.' o es None, el logger
    hereda automáticamente el handler del logger raíz de la app.
    """
    _get_app_logger()  # Asegura que el handler raíz esté inicializado
    return logging.getLogger(name or _APP_LOGGER)