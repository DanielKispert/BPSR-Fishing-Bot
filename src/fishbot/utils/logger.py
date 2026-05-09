import logging
import os
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Log directory: project_root/logs/
_LOG_DIR = Path(__file__).resolve().parent.parent.parent.parent / "logs"
_LOG_DIR.mkdir(exist_ok=True)

# --- Level detection from message prefix ---
_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "ERROR": logging.ERROR,
    "TIMEOUT": logging.WARNING,
    "GUARD RAIL": logging.WARNING,
    "RECONNECT": logging.WARNING,
    "CONTROLLER": logging.DEBUG,
}
_PREFIX_RE = re.compile(r"^\[([A-Z][A-Z0-9 _]*)\]")


def _detect_level(message):
    """Extract log level from message prefix like [INFO], [ERROR], [DEBUG], etc."""
    match = _PREFIX_RE.match(message)
    if match:
        tag = match.group(1)
        for key, level in _LEVEL_MAP.items():
            if tag.startswith(key):
                return level
    return logging.INFO


# --- Logger setup ---
_logger = logging.getLogger("fishbot")
_logger.setLevel(logging.DEBUG)
_logger.propagate = False

# Console handler: INFO and above, compact format
_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S"))

# File handler: DEBUG and above, full format, rotating
# 2 MB per file, keep 3 backups → max 8 MB on disk
_file_handler = RotatingFileHandler(
    filename=_LOG_DIR / "fishbot.log",
    maxBytes=2 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8",
)
_file_handler.setLevel(logging.DEBUG)
_file_handler.setFormatter(logging.Formatter(
    "%(asctime)s.%(msecs)03d | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
))

_logger.addHandler(_console_handler)
_logger.addHandler(_file_handler)

# Session separator on import (marks new bot run in log file)
_file_handler.stream.write("\n" + "=" * 70 + "\n")
_file_handler.stream.write(f"  NEW SESSION\n")
_file_handler.stream.write("=" * 70 + "\n\n")
_file_handler.stream.flush()


def log(message):
    """Drop-in replacement for the old log() function.
    
    Routes to the correct log level based on the message prefix:
      [DEBUG] ...     → DEBUG  (file only)
      [ERROR] ...     → ERROR
      [TIMEOUT] ...   → WARNING
      [CONTROLLER] .. → DEBUG  (file only, very verbose)
      everything else → INFO
    """
    level = _detect_level(message)
    _logger.log(level, message)
