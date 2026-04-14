"""MT5 connection helpers for live terminal and Linux mock development."""

from __future__ import annotations

import time

import pandas as pd

import config

try:
	import MetaTrader5 as mt5
except ImportError:  # pragma: no cover - used in Linux dev environments.
	import mt5_mock as mt5


def connect() -> bool:
	"""Initialize MT5 with retry logic and print connected account details.

	Retries up to config.MAX_RETRIES times, waiting config.RETRY_DELAY_SECONDS
	between attempts. Returns False and exits gracefully on exhaustion.
	"""
	for attempt in range(1, config.MAX_RETRIES + 1):
		initialized = mt5.initialize()
		if initialized:
			account = mt5.account_info()
			if account is None:
				print("MT5 connected but account info is unavailable.")
				return False
			print("MT5 connected")
			print(f"login={account.login} server={account.server} balance={account.balance}")
			return True

		error = mt5.last_error() if hasattr(mt5, "last_error") else (None, "Unknown error")
		print(f"MT5 initialization failed (attempt {attempt}/{config.MAX_RETRIES}): {error}")
		if attempt < config.MAX_RETRIES:
			print(f"Retrying in {config.RETRY_DELAY_SECONDS}s...")
			time.sleep(config.RETRY_DELAY_SECONDS)

	print("MT5 connection failed: max retries reached. Exiting.")
	return False


def disconnect() -> None:
	"""Cleanly shut down the MT5 connection."""
	mt5.shutdown()
	print("MT5 disconnected")


def get_ohlcv(symbol: str, timeframe: int, n_bars: int) -> pd.DataFrame | None:
	"""Fetch n_bars of OHLCV data for symbol/timeframe.

	Returns a pandas DataFrame with columns:
	  time, open, high, low, close, tick_volume, spread, real_volume.
	Returns None if no data is returned by MT5.
	"""
	rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n_bars)
	if not rates:
		print(f"get_ohlcv: no data returned for {symbol} tf={timeframe}")
		return None
	df = pd.DataFrame(rates)
	df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
	return df
