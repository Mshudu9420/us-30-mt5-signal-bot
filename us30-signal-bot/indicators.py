"""Indicator calculation helpers."""

from __future__ import annotations

import pandas as pd


def calculate_bollinger_bands(df: pd.DataFrame, period: int, std_dev: float) -> pd.DataFrame:
	"""Return a copy of df with Bollinger Band columns added.

	Columns added:
	- bb_mid
	- bb_upper
	- bb_lower
	"""
	result = df.copy()
	rolling_close = result["close"].rolling(window=period)
	result["bb_mid"] = rolling_close.mean()
	rolling_std = rolling_close.std()
	result["bb_upper"] = result["bb_mid"] + (rolling_std * std_dev)
	result["bb_lower"] = result["bb_mid"] - (rolling_std * std_dev)
	return result


def calculate_rsi(df: pd.DataFrame, period: int) -> pd.DataFrame:
	"""Return a copy of df with an RSI column added."""
	result = df.copy()
	delta = result["close"].diff()
	gain = delta.clip(lower=0)
	loss = -delta.clip(upper=0)

	avg_gain = gain.rolling(window=period, min_periods=period).mean()
	avg_loss = loss.rolling(window=period, min_periods=period).mean()

	rs = avg_gain / avg_loss.replace(0, pd.NA)
	result["rsi"] = 100 - (100 / (1 + rs))
	result.loc[(avg_loss == 0) & (avg_gain > 0), "rsi"] = 100.0
	result.loc[(avg_gain == 0) & (avg_loss > 0), "rsi"] = 0.0
	return result
