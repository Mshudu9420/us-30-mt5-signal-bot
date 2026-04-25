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


def calculate_ema(df: pd.DataFrame, period: int) -> pd.DataFrame:
	"""Return a copy of df with an EMA column added."""
	result = df.copy()
	result["ema"] = result["close"].ewm(span=period, adjust=False).mean()
	return result


def calculate_macd(
	df: pd.DataFrame,
	fast: int,
	slow: int,
	signal: int,
) -> pd.DataFrame:
	"""Return a copy of df with MACD columns added.

	Columns added:
	- macd           : fast EMA minus slow EMA
	- macd_signal    : EMA(signal) of the MACD line
	- macd_histogram : macd minus macd_signal (positive = bullish momentum)
	"""
	result = df.copy()
	fast_ema = result["close"].ewm(span=fast, adjust=False).mean()
	slow_ema = result["close"].ewm(span=slow, adjust=False).mean()
	result["macd"] = fast_ema - slow_ema
	result["macd_signal"] = result["macd"].ewm(span=signal, adjust=False).mean()
	result["macd_histogram"] = result["macd"] - result["macd_signal"]
	return result


def get_latest_values(df: pd.DataFrame) -> dict[str, float]:
	"""Return the latest row values needed by strategy logic."""
	latest = df.iloc[-1]
	keys = ["close", "bb_mid", "bb_upper", "bb_lower", "rsi", "ema"]
	return {key: latest[key] for key in keys if key in df.columns}


def detect_fvg(df: pd.DataFrame) -> list[dict]:
	"""Detect all Fair Value Gaps (3-candle price inefficiencies) in df.

	A Fair Value Gap forms when the range of the middle candle leaves an unfilled
	gap between the first and third candle:
	  - Bullish FVG: candle[i-2].high < candle[i].low
	  - Bearish FVG: candle[i-2].low  > candle[i].high

	Returns a list of dicts ordered by bar index (earliest first):
	  type       : 'bullish' or 'bearish'
	  top        : upper boundary of the gap
	  bottom     : lower boundary of the gap
	  time       : timestamp of the completing (third) candle
	  bar_index  : positional index of the third candle in df
	"""
	fvgs: list[dict] = []
	for i in range(2, len(df)):
		c0_high = float(df.iloc[i - 2]["high"])
		c0_low = float(df.iloc[i - 2]["low"])
		c2_high = float(df.iloc[i]["high"])
		c2_low = float(df.iloc[i]["low"])
		bar_time = df.iloc[i]["time"] if "time" in df.columns else None

		if c0_high < c2_low:  # bullish FVG — gap above first candle's high
			fvgs.append({
				"type": "bullish",
				"top": c2_low,
				"bottom": c0_high,
				"time": bar_time,
				"bar_index": i,
			})
		elif c0_low > c2_high:  # bearish FVG — gap below first candle's low
			fvgs.append({
				"type": "bearish",
				"top": c0_low,
				"bottom": c2_high,
				"time": bar_time,
				"bar_index": i,
			})
	return fvgs


def find_nearest_liquidity(
	df: pd.DataFrame,
	direction: str,
	reference_price: float,
	tolerance_pct: float = 0.001,
) -> float | None:
	"""Find the nearest liquidity level (relative equal highs or lows) to reference_price.

	Liquidity is defined as two or more candle wick tips clustered within
	tolerance_pct of each other.

	- BULLISH direction: scan equal highs ABOVE reference_price (buy-side target).
	- BEARISH direction: scan equal lows  BELOW reference_price (sell-side target).

	Returns the mean price of the nearest cluster, or None if no cluster found.
	"""
	tolerance = reference_price * tolerance_pct

	if direction == "BULLISH":
		raw = sorted(float(v) for v in df["high"].dropna() if float(v) > reference_price)
	else:
		raw = sorted(float(v) for v in df["low"].dropna() if float(v) < reference_price)

	if not raw:
		return None

	# Group consecutive values into clusters where all values are within tolerance
	clusters: list[list[float]] = []
	current: list[float] = [raw[0]]
	for level in raw[1:]:
		if level - current[0] <= tolerance:
			current.append(level)
		else:
			clusters.append(current)
			current = [level]
	clusters.append(current)

	# Liquidity requires at least 2 equal wick tips
	liquidity_clusters = [c for c in clusters if len(c) >= 2]
	if not liquidity_clusters:
		return None

	# Nearest cluster to reference_price
	if direction == "BULLISH":
		nearest = min(liquidity_clusters, key=lambda c: min(c))
	else:
		nearest = max(liquidity_clusters, key=lambda c: max(c))

	return round(sum(nearest) / len(nearest), 2)
