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
