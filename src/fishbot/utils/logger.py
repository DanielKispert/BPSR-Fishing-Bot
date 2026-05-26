import logging
import os
import re
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Log directory: next to exe (frozen) or project_root/logs/ (dev)
if getattr(sys, 'frozen', False):
    _LOG_DIR = Path(sys.executable).parent / "logs"
else:
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
_log_file = _LOG_DIR / "fishbot.log"
# Clear log on each bot start
if _log_file.exists():
    _log_file.write_text("", encoding="utf-8")
_file_handler = RotatingFileHandler(
    filename=_log_file,
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
