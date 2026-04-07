"""
Logging configuration for the Otocyon framework.

Uses structlog for structured, context-bound log output. The processor chain
is wired to stdlib so any third-party library using ``logging`` still flows
through the same pipeline.

Swap ``ConsoleRenderer`` for ``JSONRenderer`` (or ``LogfmtRenderer``) in
production / log-shipping environments without changing any call sites.
"""

import logging

import structlog


def configure_logging(level: int = logging.INFO) -> None:
    """
    Configure structlog with a stdlib-backed processor chain.

    Call once at process startup (e.g. in ``runner.py``) before constructing
    any ``Context``.

    Args:
        level: stdlib log level to capture (default ``logging.INFO``).
    """
    logging.basicConfig(format="%(message)s", level=level)

    structlog.configure(
        processors=[
            # Merge thread-local context vars into every log entry
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            # ↓ Swap for JSONRenderer or LogfmtRenderer in production
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "otocyon") -> structlog.stdlib.BoundLogger:
    """
    Return a structlog BoundLogger for the given name.

    The returned logger supports ``.bind(**fields)`` to attach structured
    key-value pairs to every subsequent log call::

        log = get_logger("engine").bind(strategy="TrendFollower", step=42)
        log.info("sensor_pass.complete", indicators=5)
    """
    return structlog.get_logger(name)  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# NO_LOGGER — a safe silent default used when no Context has been configured.
# Wraps a stdlib NullHandler logger so all output is silently discarded.
# ---------------------------------------------------------------------------
_null_stdlib = logging.getLogger("otocyon.null")
_null_stdlib.addHandler(logging.NullHandler())
_null_stdlib.propagate = False
_null_stdlib.setLevel(logging.CRITICAL + 1)

NO_LOGGER: structlog.stdlib.BoundLogger = structlog.wrap_logger(_null_stdlib)
