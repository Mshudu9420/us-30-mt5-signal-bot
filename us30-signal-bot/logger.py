"""Centralised logging setup for the US30 MT5 signal bot.

Call `get_logger()` from any module to obtain the shared bot logger.
The logger writes to:
  - The terminal  (StreamHandler, INFO+)
  - logs/bot.csv  (RotatingFileHandler, DEBUG+, CSV format)

CSV columns: timestamp, level, message
Rotation policy (from config):
  - Max file size : LOG_MAX_BYTES  (default 10 MB)
  - Backup count  : LOG_BACKUP_COUNT (default 7 — roughly one week)
"""

from __future__ import annotations

import csv
import io
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

import config

_LOGGER_NAME = "us30-bot"
_STREAM_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_CSV_HEADER = ["timestamp", "level", "message"]

_logger: logging.Logger | None = None


class _CsvFormatter(logging.Formatter):
	"""Format each log record as a single CSV row (no trailing newline)."""

	def format(self, record: logging.LogRecord) -> str:
		buf = io.StringIO()
		writer = csv.writer(buf, quoting=csv.QUOTE_MINIMAL)
		writer.writerow([
			self.formatTime(record, self.datefmt),
			record.levelname,
			record.getMessage(),
		])
		return buf.getvalue().rstrip("\r\n")


class _StdoutHandler(logging.StreamHandler):
	"""StreamHandler that resolves sys.stdout at emit time (compatible with pytest capsys)."""

	@property  # type: ignore[override]
	def stream(self):  # type: ignore[override]
		return sys.stdout

	@stream.setter
	def stream(self, value) -> None:
		pass  # always delegate to sys.stdout; ignore stored value


def get_logger() -> logging.Logger:
	"""Return the shared bot logger, initialising it on first call."""
	global _logger
	if _logger is not None:
		return _logger

	logger = logging.getLogger(_LOGGER_NAME)
	logger.setLevel(logging.DEBUG)

	# Avoid adding duplicate handlers if get_logger() is somehow called twice
	if logger.handlers:
		_logger = logger
		return logger

	# --- Terminal handler (plain text, INFO+, dynamic stdout for pytest capsys) ---
	stream_handler = _StdoutHandler()
	stream_handler.setLevel(logging.INFO)
	stream_handler.setFormatter(logging.Formatter(_STREAM_FORMAT, datefmt=_DATE_FORMAT))
	logger.addHandler(stream_handler)

	# --- Rotating CSV file handler (DEBUG+) ---
	log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), config.LOG_DIR)
	os.makedirs(log_dir, exist_ok=True)
	csv_path = os.path.join(log_dir, "bot.csv")

	# Write CSV header only when creating a new file
	if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
		with open(csv_path, "w", newline="", encoding="utf-8") as _f:
			csv.writer(_f).writerow(_CSV_HEADER)

	csv_handler = RotatingFileHandler(
		csv_path,
		maxBytes=config.LOG_MAX_BYTES,
		backupCount=config.LOG_BACKUP_COUNT,
		encoding="utf-8",
	)
	csv_handler.setLevel(logging.DEBUG)
	csv_handler.setFormatter(_CsvFormatter(datefmt=_DATE_FORMAT))
	logger.addHandler(csv_handler)

	_logger = logger
	return logger
