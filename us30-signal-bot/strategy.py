"""Trading signal strategy helpers."""

from __future__ import annotations

import pandas as pd


def get_h1_bias(h1_df: pd.DataFrame) -> str:
	"""Return H1 trend bias from the latest close vs EMA value."""
	latest = h1_df.iloc[-1]
	close = latest["close"]
	ema = latest["ema"]

	if pd.isna(close) or pd.isna(ema) or close == ema:
		return "UNCLEAR"
	if close > ema:
		return "BULLISH"
	return "BEARISH"


def check_signal(df: pd.DataFrame, timeframe: str, h1_bias: str) -> dict[str, object] | None:
	"""Return a mean-reversion signal filtered by H1 trend bias."""
	latest = df.iloc[-1]
	close = latest["close"]
	rsi = latest["rsi"]
	bb_lower = latest["bb_lower"]
	bb_upper = latest["bb_upper"]
	timestamp = latest.get("time")

	if h1_bias == "UNCLEAR":
		return None

	if close < bb_lower and rsi < 30:
		if h1_bias == "BEARISH":
			return None
		return {
			"direction": "BUY",
			"timeframe": timeframe,
			"entry_price": close,
			"timestamp": timestamp,
		}

	if close > bb_upper and rsi > 70:
		if h1_bias == "BULLISH":
			return None
		return {
			"direction": "SELL",
			"timeframe": timeframe,
			"entry_price": close,
			"timestamp": timestamp,
		}

	return None


def is_high_confidence(m5_signal: dict[str, object] | None, m15_signal: dict[str, object] | None) -> bool:
	"""Return True when M5 and M15 signals both exist and match direction."""
	if not m5_signal or not m15_signal:
		return False
	return m5_signal.get("direction") == m15_signal.get("direction")
