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
