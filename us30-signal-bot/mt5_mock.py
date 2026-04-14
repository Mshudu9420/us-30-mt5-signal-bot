"""Linux-friendly stub that mimics a subset of MetaTrader5 behavior.

This module provides the interfaces required by Task 2.1 so connector code can
be developed and unit-tested without a live MT5 terminal.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any


# Minimal timeframe constants used by the strategy.
TIMEFRAME_M5 = 5
TIMEFRAME_M15 = 15
TIMEFRAME_H1 = 60


@dataclass(frozen=True)
class AccountInfo:
	login: int
	server: str
	balance: float


_initialized = False
_last_error: tuple[int, str] = (0, "Success")


def initialize(*args: Any, **kwargs: Any) -> bool:
	"""Mimic MT5 initialize call.

	Always succeeds in the mock and flips internal connection state on.
	"""
	global _initialized, _last_error
	_initialized = True
	_last_error = (0, "Success")
	return True


def shutdown() -> bool:
	"""Mimic MT5 shutdown call."""
	global _initialized
	_initialized = False
	return True


def account_info() -> AccountInfo | None:
	"""Return deterministic account details while initialized."""
	if not _initialized:
		return None
	return AccountInfo(login=12345678, server="Exness-Demo", balance=1000.00)


def copy_rates_from_pos(symbol: str, timeframe: int, start_pos: int, count: int) -> list[dict[str, Any]]:
	"""Return synthetic OHLCV bars in a MetaTrader5-compatible shape.

	The payload keys mirror MT5 rate fields so downstream code can convert
	directly into a pandas DataFrame.
	"""
	if not _initialized:
		_set_error(10001, "Not initialized")
		return []

	minutes = _timeframe_to_minutes(timeframe)
	now = datetime.now(tz=timezone.utc).replace(second=0, microsecond=0)
	bars: list[dict[str, Any]] = []

	for i in range(count):
		idx = start_pos + i
		candle_time = now - timedelta(minutes=minutes * (count - i))

		# Deterministic synthetic candle data around a US30-like price level.
		base = 39000.0 + (idx * 0.5)
		open_price = round(base, 2)
		close_price = round(base + ((-1) ** idx) * 1.2, 2)
		high_price = round(max(open_price, close_price) + 0.8, 2)
		low_price = round(min(open_price, close_price) - 0.8, 2)

		bars.append(
			{
				"time": int(candle_time.timestamp()),
				"open": open_price,
				"high": high_price,
				"low": low_price,
				"close": close_price,
				"tick_volume": 100 + idx,
				"spread": 20,
				"real_volume": 0,
			}
		)

	_set_error(0, "Success")
	return bars


def last_error() -> tuple[int, str]:
	"""Return the latest mock error tuple."""
	return _last_error


def version() -> tuple[int, int, str]:
	"""Return a mock terminal version tuple."""
	return (500, 0, "MT5-MOCK")


def _timeframe_to_minutes(timeframe: int) -> int:
	if timeframe == TIMEFRAME_M5:
		return 5
	if timeframe == TIMEFRAME_M15:
		return 15
	if timeframe == TIMEFRAME_H1:
		return 60
	return 1


def _set_error(code: int, message: str) -> None:
	global _last_error
	_last_error = (code, message)
