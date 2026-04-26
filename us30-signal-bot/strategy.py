"""Trading signal strategy helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas as pd

from indicators import find_nearest_liquidity


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


def is_in_trading_session(now: datetime | None = None, symbol: str = "") -> bool:
	"""Return True if trading is allowed for *symbol* at *now*.

	24/7 instruments (BTC, ETH, etc.) listed in ``config.SESSION_EXEMPT_SYMBOLS``
	always return True regardless of the time.  All other symbols must fall
	within the configured New York session window (09:30–16:00 ET).
	DST transitions are handled automatically by ``zoneinfo``.

	Parameters
	----------
	now:
		Reference timestamp.  If ``None``, the current UTC wall-clock time is
		used.  Pass a timezone-aware ``datetime`` for testing.
	symbol:
		Broker symbol string (e.g. ``"BTCUSDm"``).  Case-insensitive substring
		match against ``config.SESSION_EXEMPT_SYMBOLS``.
	"""
	import config as _cfg

	# Exempt 24/7 instruments from the session gate entirely.
	symbol_lower = symbol.lower()
	if any(exempt in symbol_lower for exempt in _cfg.SESSION_EXEMPT_SYMBOLS):
		return True

	if now is None:
		now = datetime.now(tz=timezone.utc)
	elif now.tzinfo is None:
		now = now.replace(tzinfo=timezone.utc)

	ny_tz = ZoneInfo(_cfg.TRADING_SESSION_TZ)
	ny_now = now.astimezone(ny_tz)

	start_h, start_m = _cfg.TRADING_SESSION_START
	end_h, end_m = _cfg.TRADING_SESSION_END

	session_start = ny_now.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
	session_end = ny_now.replace(hour=end_h, minute=end_m, second=0, microsecond=0)

	return session_start <= ny_now < session_end


def check_signal(df: pd.DataFrame, timeframe: str, h1_bias: str) -> dict[str, object] | None:
	"""Return a mean-reversion signal filtered by H1 trend bias and MACD momentum.

	MACD confirmation (soft gate): when the `macd_histogram` column is present,
	a BUY is only returned when the histogram is rising (current > previous bar)
	and a SELL only when it is falling (current < previous bar).  If the column
	is absent the MACD check is skipped so that tests and callers that do not
	compute MACD continue to work unchanged.
	"""
	latest = df.iloc[-1]
	close = latest["close"]
	rsi = latest["rsi"]
	bb_lower = latest["bb_lower"]
	bb_upper = latest["bb_upper"]
	timestamp = latest.get("time")

	if h1_bias == "UNCLEAR":
		return None

	# Determine MACD histogram direction when the column is available.
	_macd_rising: bool | None = None
	if "macd_histogram" in df.columns and len(df) >= 2:
		h_now = float(df.iloc[-1]["macd_histogram"])
		h_prev = float(df.iloc[-2]["macd_histogram"])
		if not (pd.isna(h_now) or pd.isna(h_prev)):
			_macd_rising = h_now > h_prev

	if close < bb_lower and rsi < 30:
		if h1_bias == "BEARISH":
			return None
		# MACD gate: skip if histogram is confirmed falling (not rising)
		if _macd_rising is False:
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
		# MACD gate: skip if histogram is confirmed rising (not falling)
		if _macd_rising is True:
			return None
		return {
			"direction": "SELL",
			"timeframe": timeframe,
			"entry_price": close,
			"timestamp": timestamp,
		}

	return None



def is_high_confidence(
    m1_signal: dict[str, object] | None,
    m5_signal: dict[str, object] | None,
    m15_signal: dict[str, object] | None,
    h1_bias: str,
) -> bool:
	"""Return True when M1 and M5 agree and M15 and H1 match the same direction.

	Rules:
	- M1 and M5 must both exist and have the same `direction`.
	- M15 must exist and have the same `direction` as M1/M5.
	- H1 bias must match the direction (BUY -> BULLISH, SELL -> BEARISH).
	"""
	if not m1_signal or not m5_signal or not m15_signal:
		return False
	dir1 = m1_signal.get("direction")
	dir5 = m5_signal.get("direction")
	dir15 = m15_signal.get("direction")
	if dir1 != dir5 or dir1 != dir15:
		return False
	# Map direction to H1 bias
	if dir1 == "BUY" and h1_bias == "BULLISH":
		return True
	if dir1 == "SELL" and h1_bias == "BEARISH":
		return True
	return False


def is_medium_confidence(
    m5_signal: dict[str, object] | None,
    m15_signal: dict[str, object] | None,
    h1_bias: str,
) -> bool:
	"""Return True when M5 and M15 agree and H1 bias matches (M1 not required).

	This tier fires more frequently than high-confidence and triggers an alert
	only (no auto-trade). Lot size is reduced by MEDIUM_CONFIDENCE_LOT_MULTIPLIER.

	Rules:
	- M5 and M15 must both exist and share the same `direction`.
	- H1 bias must match the direction (BUY -> BULLISH, SELL -> BEARISH).
	"""
	if not m5_signal or not m15_signal:
		return False
	dir5 = m5_signal.get("direction")
	dir15 = m15_signal.get("direction")
	if dir5 != dir15:
		return False
	if dir5 == "BUY" and h1_bias == "BULLISH":
		return True
	if dir5 == "SELL" and h1_bias == "BEARISH":
		return True
	return False


# ---------------------------------------------------------------------------
# Macro-time Fair Value Gap analysis
# ---------------------------------------------------------------------------

def get_last_completed_macro_window(now: datetime) -> tuple[datetime, datetime]:
	"""Return (macro_start, macro_end) for the most recently completed macro window.

	A macro window spans 10 minutes before to 10 minutes after the top of each
	hour (e.g. 00:50–01:10, 01:50–02:10, ...). 'Completed' means macro_end < now.
	"""
	hour_top = now.replace(minute=0, second=0, microsecond=0)
	macro_end = hour_top + timedelta(minutes=10)
	if now >= macro_end:
		# Current hour's macro has already ended
		return hour_top - timedelta(minutes=10), macro_end
	# Current hour's macro is still in progress — use the previous hour
	prev_hour_top = hour_top - timedelta(hours=1)
	return prev_hour_top - timedelta(minutes=10), prev_hour_top + timedelta(minutes=10)


def is_in_macro_window(now: datetime) -> bool:
	"""Return True when now falls within any 20-minute macro window (HH:50–HH+1:10)."""
	hour_top = now.replace(minute=0, second=0, microsecond=0)
	# Check window centred on current hour top
	if hour_top - timedelta(minutes=10) <= now <= hour_top + timedelta(minutes=10):
		return True
	# Check window centred on next hour top (covers :50–:59 before the next hour)
	next_hour_top = hour_top + timedelta(hours=1)
	return next_hour_top - timedelta(minutes=10) <= now <= next_hour_top + timedelta(minutes=10)


def get_macro_fvg_signal(
	m1_df: pd.DataFrame,
	fvgs: list[dict],
	now: datetime,
) -> dict[str, object] | None:
	"""Analyse the first M1 FVG from the last completed macro window and return a signal.

	Steps:
	1. Determine the last completed macro window.
	2. Find the first FVG whose completing candle falls inside that window.
	3. Examine post-macro M1 candles:
	   - Any candle HIGH above the FVG top  → BULLISH (price confirmed above gap).
	   - No candle above the FVG top        → BEARISH (price failed to reclaim gap).
	4. Seek the nearest liquidity:
	   - BULLISH → equal highs above current price (buy-side target).
	   - BEARISH → equal lows  below current price (sell-side target).
	5. Return a signal dict, or None when no qualifying FVG is found.
	"""
	if m1_df is None or not fvgs:
		return None

	macro_start, macro_end = get_last_completed_macro_window(now)
	_ms = pd.Timestamp(macro_start)
	_me = pd.Timestamp(macro_end)

	# First FVG whose completing candle time falls within the macro window
	macro_fvgs = [
		fvg for fvg in fvgs
		if fvg["time"] is not None and _ms <= pd.Timestamp(fvg["time"]) <= _me
	]
	if not macro_fvgs:
		return None

	first_fvg = macro_fvgs[0]
	fvg_top = first_fvg["top"]
	fvg_bottom = first_fvg["bottom"]

	# Post-macro candles — bars whose time is strictly after macro_end
	post_macro = m1_df[m1_df["time"].apply(pd.Timestamp) > _me]
	if post_macro.empty:
		return None  # macro hasn't fully closed yet or no M1 data after it

	latest_close = float(m1_df.iloc[-1]["close"])

	# Determine direction from post-macro price action relative to the FVG
	candle_above_fvg = bool((post_macro["high"] > fvg_top).any())
	direction = "BULLISH" if candle_above_fvg else "BEARISH"

	liquidity_target = find_nearest_liquidity(m1_df, direction, latest_close)

	return {
		"source": "macro_fvg",
		"direction": direction,
		"fvg_top": round(fvg_top, 2),
		"fvg_bottom": round(fvg_bottom, 2),
		"fvg_type": first_fvg["type"],
		"macro_start": str(macro_start),
		"macro_end": str(macro_end),
		"liquidity_target": liquidity_target,
		"entry_price": round(latest_close, 2),
		"timeframe": "M1",
	}
