# Ported from appevidence/evidence-capture-app at commit 6b5b998a71a5891112701381d76c7bd34974e53d
from __future__ import annotations

import logging

_LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"


def configure_logging(level: str = "INFO") -> None:
    """Configure the root logger with a standard format."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=_LOG_FORMAT,
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    """Return a named logger."""
    return logging.getLogger(name)
