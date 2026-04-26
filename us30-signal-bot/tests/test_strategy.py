import pandas as pd

import strategy


def test_get_h1_bias_returns_bullish_when_close_above_ema():
	h1_df = pd.DataFrame({"close": [39000.0], "ema": [38950.0]})

	result = strategy.get_h1_bias(h1_df)

	assert result == "BULLISH"


def test_get_h1_bias_returns_bearish_when_close_below_ema():
	h1_df = pd.DataFrame({"close": [38900.0], "ema": [38950.0]})

	result = strategy.get_h1_bias(h1_df)

	assert result == "BEARISH"


def test_get_h1_bias_returns_unclear_when_close_equals_ema():
	h1_df = pd.DataFrame({"close": [38950.0], "ema": [38950.0]})

	result = strategy.get_h1_bias(h1_df)

	assert result == "UNCLEAR"


def test_check_signal_returns_buy_signal_when_oversold_below_lower_band():
	df = pd.DataFrame(
		{
			"time": ["2026-04-14 10:00:00"],
			"close": [38900.0],
			"rsi": [25.0],
			"bb_lower": [38950.0],
			"bb_upper": [39150.0],
		}
	)

	result = strategy.check_signal(df, timeframe="M5", h1_bias="BULLISH")

	assert result == {
		"direction": "BUY",
		"timeframe": "M5",
		"entry_price": 38900.0,
		"timestamp": "2026-04-14 10:00:00",
	}


def test_check_signal_returns_sell_signal_when_overbought_above_upper_band():
	df = pd.DataFrame(
		{
			"time": ["2026-04-14 10:05:00"],
			"close": [39200.0],
			"rsi": [75.0],
			"bb_lower": [38950.0],
			"bb_upper": [39150.0],
		}
	)

	result = strategy.check_signal(df, timeframe="M15", h1_bias="BEARISH")

	assert result == {
		"direction": "SELL",
		"timeframe": "M15",
		"entry_price": 39200.0,
		"timestamp": "2026-04-14 10:05:00",
	}


def test_check_signal_returns_none_when_conditions_are_not_met():
	df = pd.DataFrame(
		{
			"time": ["2026-04-14 10:10:00"],
			"close": [39020.0],
			"rsi": [50.0],
			"bb_lower": [38950.0],
			"bb_upper": [39150.0],
		}
	)

	result = strategy.check_signal(df, timeframe="M5", h1_bias="UNCLEAR")

	assert result is None


def test_check_signal_suppresses_buy_when_h1_bias_is_bearish():
	df = pd.DataFrame(
		{
			"time": ["2026-04-14 10:15:00"],
			"close": [38900.0],
			"rsi": [25.0],
			"bb_lower": [38950.0],
			"bb_upper": [39150.0],
		}
	)

	result = strategy.check_signal(df, timeframe="M5", h1_bias="BEARISH")

	assert result is None


def test_check_signal_suppresses_sell_when_h1_bias_is_bullish():
	df = pd.DataFrame(
		{
			"time": ["2026-04-14 10:20:00"],
			"close": [39200.0],
			"rsi": [75.0],
			"bb_lower": [38950.0],
			"bb_upper": [39150.0],
		}
	)

	result = strategy.check_signal(df, timeframe="M15", h1_bias="BULLISH")

	assert result is None


def test_check_signal_suppresses_all_signals_when_h1_bias_unclear():
	df = pd.DataFrame(
		{
			"time": ["2026-04-14 10:25:00"],
			"close": [39200.0],
			"rsi": [75.0],
			"bb_lower": [38950.0],
			"bb_upper": [39150.0],
		}
	)

	result = strategy.check_signal(df, timeframe="M15", h1_bias="UNCLEAR")

	assert result is None


def test_is_high_confidence_true_when_m1_m5_m15_and_h1_agree():
	m1_signal = {"direction": "BUY", "timeframe": "M1"}
	m5_signal = {"direction": "BUY", "timeframe": "M5"}
	m15_signal = {"direction": "BUY", "timeframe": "M15"}

	result = strategy.is_high_confidence(m1_signal, m5_signal, m15_signal, "BULLISH")

	assert result is True


def test_is_high_confidence_false_when_directions_differ():
	m1_signal = {"direction": "BUY", "timeframe": "M1"}
	m5_signal = {"direction": "BUY", "timeframe": "M5"}
	m15_signal = {"direction": "SELL", "timeframe": "M15"}

	result = strategy.is_high_confidence(m1_signal, m5_signal, m15_signal, "BULLISH")

	assert result is False


def test_is_high_confidence_false_when_any_signal_missing():
	# Missing m1
	result_missing_m1 = strategy.is_high_confidence(None, {"direction": "BUY"}, {"direction": "BUY"}, "BULLISH")
	# Missing m5
	result_missing_m5 = strategy.is_high_confidence({"direction": "BUY"}, None, {"direction": "BUY"}, "BULLISH")
	# Missing m15
	result_missing_m15 = strategy.is_high_confidence({"direction": "BUY"}, {"direction": "BUY"}, None, "BULLISH")

	assert result_missing_m1 is False
	assert result_missing_m5 is False
	assert result_missing_m15 is False


# --- Medium-confidence tests ---

def test_is_medium_confidence_true_when_m5_m15_and_h1_agree_buy():
	m5_signal = {"direction": "BUY", "timeframe": "M5"}
	m15_signal = {"direction": "BUY", "timeframe": "M15"}

	result = strategy.is_medium_confidence(m5_signal, m15_signal, "BULLISH")

	assert result is True


def test_is_medium_confidence_true_when_m5_m15_and_h1_agree_sell():
	m5_signal = {"direction": "SELL", "timeframe": "M5"}
	m15_signal = {"direction": "SELL", "timeframe": "M15"}

	result = strategy.is_medium_confidence(m5_signal, m15_signal, "BEARISH")

	assert result is True


def test_is_medium_confidence_false_when_m5_and_m15_directions_differ():
	m5_signal = {"direction": "BUY", "timeframe": "M5"}
	m15_signal = {"direction": "SELL", "timeframe": "M15"}

	result = strategy.is_medium_confidence(m5_signal, m15_signal, "BULLISH")

	assert result is False


def test_is_medium_confidence_false_when_h1_bias_does_not_match():
	m5_signal = {"direction": "BUY", "timeframe": "M5"}
	m15_signal = {"direction": "BUY", "timeframe": "M15"}

	# H1 says BEARISH — should not confirm a BUY
	result = strategy.is_medium_confidence(m5_signal, m15_signal, "BEARISH")

	assert result is False


def test_is_medium_confidence_false_when_h1_bias_unclear():
	m5_signal = {"direction": "BUY", "timeframe": "M5"}
	m15_signal = {"direction": "BUY", "timeframe": "M15"}

	result = strategy.is_medium_confidence(m5_signal, m15_signal, "UNCLEAR")

	assert result is False


def test_is_medium_confidence_false_when_either_signal_missing():
	assert strategy.is_medium_confidence(None, {"direction": "BUY"}, "BULLISH") is False
	assert strategy.is_medium_confidence({"direction": "BUY"}, None, "BULLISH") is False


def test_is_medium_confidence_fires_without_m1():
	"""Medium-confidence must not require M1 — M5+M15+H1 alone is sufficient."""
	m5_signal = {"direction": "SELL", "timeframe": "M5"}
	m15_signal = {"direction": "SELL", "timeframe": "M15"}

	# No m1 signal — should still return True
	result = strategy.is_medium_confidence(m5_signal, m15_signal, "BEARISH")

	assert result is True


# ---------------------------------------------------------------------------
# Macro FVG tests
# ---------------------------------------------------------------------------

from datetime import datetime, timedelta, timezone


def _make_m1_df_with_times(base_time: datetime, prices: list[dict]) -> pd.DataFrame:
	"""Build a minimal M1 OHLCV DataFrame with pd.Timestamp time column."""
	rows = []
	for i, p in enumerate(prices):
		rows.append({
			"time": pd.Timestamp(base_time + timedelta(minutes=i)),
			"open": p["open"],
			"high": p["high"],
			"low": p["low"],
			"close": p["close"],
		})
	return pd.DataFrame(rows)


def test_get_last_completed_macro_window_returns_current_hour_when_past_10():
	# 01:25 — current hour's macro (00:50–01:10) has ended
	now = datetime(2026, 4, 25, 1, 25, tzinfo=timezone.utc)
	start, end = strategy.get_last_completed_macro_window(now)
	assert start == datetime(2026, 4, 25, 0, 50, tzinfo=timezone.utc)
	assert end == datetime(2026, 4, 25, 1, 10, tzinfo=timezone.utc)


def test_get_last_completed_macro_window_returns_prev_hour_when_inside_window():
	# 01:05 — current hour's macro (00:50–01:10) is still in progress
	now = datetime(2026, 4, 25, 1, 5, tzinfo=timezone.utc)
	start, end = strategy.get_last_completed_macro_window(now)
	assert start == datetime(2026, 4, 24, 23, 50, tzinfo=timezone.utc)
	assert end == datetime(2026, 4, 25, 0, 10, tzinfo=timezone.utc)


def test_is_in_macro_window_true_at_50_minutes():
	now = datetime(2026, 4, 25, 0, 50, tzinfo=timezone.utc)
	assert strategy.is_in_macro_window(now) is True


def test_is_in_macro_window_true_at_10_past():
	now = datetime(2026, 4, 25, 1, 10, tzinfo=timezone.utc)
	assert strategy.is_in_macro_window(now) is True


def test_is_in_macro_window_false_outside_window():
	now = datetime(2026, 4, 25, 1, 30, tzinfo=timezone.utc)
	assert strategy.is_in_macro_window(now) is False


def test_get_macro_fvg_signal_returns_bullish_when_price_prints_above_fvg():
	# Macro window: 00:50–01:10 UTC
	# FVG completing candle at 01:00 (inside window): bullish FVG top=102, bottom=100
	# Post-macro candle at 01:15 has high=105 > fvg_top=102 → BULLISH
	base = datetime(2026, 4, 25, 0, 58, tzinfo=timezone.utc)
	prices = [
		# candle 0 (0:58) — FVG first candle, high=100
		{"open": 98, "high": 100, "low": 97, "close": 99},
		# candle 1 (0:59) — FVG middle candle
		{"open": 99, "high": 101, "low": 98, "close": 100},
		# candle 2 (1:00) — FVG third candle, low=102 → bullish FVG [100, 102]
		{"open": 102, "high": 106, "low": 102, "close": 104},
		# candle 3 (1:01) — still inside macro, irrelevant
		{"open": 104, "high": 106, "low": 103, "close": 105},
		# candle 4 (1:02–1:10 gap) — post-macro candle (time set manually below)
		{"open": 103, "high": 105, "low": 102, "close": 104},
	]
	df = _make_m1_df_with_times(base, prices)
	# Push last candle's time to post-macro (1:15)
	df.at[4, "time"] = pd.Timestamp(datetime(2026, 4, 25, 1, 15, tzinfo=timezone.utc))

	from indicators import detect_fvg
	fvgs = detect_fvg(df)

	now = datetime(2026, 4, 25, 1, 25, tzinfo=timezone.utc)
	result = strategy.get_macro_fvg_signal(df, fvgs, now)

	assert result is not None
	assert result["direction"] == "BULLISH"
	assert result["fvg_type"] == "bullish"


def test_get_macro_fvg_signal_returns_bearish_when_price_fails_above_fvg():
	# Same FVG as above, but post-macro candle never exceeds fvg_top=102
	base = datetime(2026, 4, 25, 0, 58, tzinfo=timezone.utc)
	prices = [
		{"open": 98, "high": 100, "low": 97, "close": 99},
		{"open": 99, "high": 101, "low": 98, "close": 100},
		{"open": 102, "high": 106, "low": 102, "close": 104},
		{"open": 104, "high": 106, "low": 103, "close": 105},
		# post-macro candle high=101 — below fvg_top=102 → BEARISH
		{"open": 101, "high": 101, "low": 99, "close": 100},
	]
	df = _make_m1_df_with_times(base, prices)
	df.at[4, "time"] = pd.Timestamp(datetime(2026, 4, 25, 1, 15, tzinfo=timezone.utc))

	from indicators import detect_fvg
	fvgs = detect_fvg(df)

	now = datetime(2026, 4, 25, 1, 25, tzinfo=timezone.utc)
	result = strategy.get_macro_fvg_signal(df, fvgs, now)

	assert result is not None
	assert result["direction"] == "BEARISH"


def test_get_macro_fvg_signal_returns_none_when_no_fvg_in_window():
	# All candles overlap — no FVG formed
	base = datetime(2026, 4, 25, 0, 58, tzinfo=timezone.utc)
	prices = [
		{"open": 100, "high": 102, "low": 99, "close": 101},
		{"open": 101, "high": 103, "low": 100, "close": 102},
		{"open": 102, "high": 104, "low": 101, "close": 103},
	]
	df = _make_m1_df_with_times(base, prices)

	from indicators import detect_fvg
	fvgs = detect_fvg(df)

	now = datetime(2026, 4, 25, 1, 25, tzinfo=timezone.utc)
	result = strategy.get_macro_fvg_signal(df, fvgs, now)

	assert result is None


def test_get_macro_fvg_signal_returns_none_when_no_post_macro_data():
	# FVG exists in window but no candles after macro_end yet
	base = datetime(2026, 4, 25, 0, 58, tzinfo=timezone.utc)
	prices = [
		{"open": 98, "high": 100, "low": 97, "close": 99},
		{"open": 99, "high": 101, "low": 98, "close": 100},
		{"open": 102, "high": 106, "low": 102, "close": 104},
	]
	df = _make_m1_df_with_times(base, prices)

	from indicators import detect_fvg
	fvgs = detect_fvg(df)

	# now = 1:08, still inside the macro window (00:50–01:10) → no post-macro data
	now = datetime(2026, 4, 25, 1, 8, tzinfo=timezone.utc)
	result = strategy.get_macro_fvg_signal(df, fvgs, now)

	assert result is None


# --- MACD confirmation in check_signal ---

def _buy_df(macd_histogram_prev: float, macd_histogram_curr: float) -> pd.DataFrame:
	"""Build a 2-row DataFrame that triggers a BUY on the last row with given MACD histogram values."""
	return pd.DataFrame({
		"time": ["2026-04-14 10:00:00", "2026-04-14 10:01:00"],
		"close": [38900.0, 38900.0],
		"rsi": [25.0, 25.0],
		"bb_lower": [38950.0, 38950.0],
		"bb_upper": [39150.0, 39150.0],
		"macd_histogram": [macd_histogram_prev, macd_histogram_curr],
	})


def _sell_df(macd_histogram_prev: float, macd_histogram_curr: float) -> pd.DataFrame:
	"""Build a 2-row DataFrame that triggers a SELL on the last row with given MACD histogram values."""
	return pd.DataFrame({
		"time": ["2026-04-14 10:00:00", "2026-04-14 10:01:00"],
		"close": [39200.0, 39200.0],
		"rsi": [75.0, 75.0],
		"bb_lower": [38950.0, 38950.0],
		"bb_upper": [39150.0, 39150.0],
		"macd_histogram": [macd_histogram_prev, macd_histogram_curr],
	})


def test_check_signal_buy_passes_when_macd_histogram_rising():
	df = _buy_df(macd_histogram_prev=-0.5, macd_histogram_curr=0.2)

	result = strategy.check_signal(df, timeframe="M5", h1_bias="BULLISH")

	assert result is not None
	assert result["direction"] == "BUY"


def test_check_signal_buy_blocked_when_macd_histogram_falling():
	df = _buy_df(macd_histogram_prev=0.5, macd_histogram_curr=-0.2)

	result = strategy.check_signal(df, timeframe="M5", h1_bias="BULLISH")

	assert result is None


def test_check_signal_sell_passes_when_macd_histogram_falling():
	df = _sell_df(macd_histogram_prev=0.5, macd_histogram_curr=-0.2)

	result = strategy.check_signal(df, timeframe="M15", h1_bias="BEARISH")

	assert result is not None
	assert result["direction"] == "SELL"


def test_check_signal_sell_blocked_when_macd_histogram_rising():
	df = _sell_df(macd_histogram_prev=-0.5, macd_histogram_curr=0.2)

	result = strategy.check_signal(df, timeframe="M15", h1_bias="BEARISH")

	assert result is None


def test_check_signal_buy_passes_when_macd_column_absent():
	"""Soft gate: no macd_histogram column → MACD check is skipped."""
	df = pd.DataFrame({
		"time": ["2026-04-14 10:00:00"],
		"close": [38900.0],
		"rsi": [25.0],
		"bb_lower": [38950.0],
		"bb_upper": [39150.0],
	})

	result = strategy.check_signal(df, timeframe="M5", h1_bias="BULLISH")

	assert result is not None
	assert result["direction"] == "BUY"


# ---------------------------------------------------------------------------
# NY trading session filter
# ---------------------------------------------------------------------------

def _ny(hour: int, minute: int = 0) -> datetime:
	"""Return a timezone-aware datetime at the given NY (ET) wall-clock time."""
	from zoneinfo import ZoneInfo
	return datetime(2026, 4, 26, hour, minute, tzinfo=ZoneInfo("America/New_York"))


def test_is_in_trading_session_true_at_open():
	assert strategy.is_in_trading_session(_ny(9, 30)) is True


def test_is_in_trading_session_true_during_session():
	assert strategy.is_in_trading_session(_ny(12, 0)) is True


def test_is_in_trading_session_true_one_minute_before_close():
	assert strategy.is_in_trading_session(_ny(15, 59)) is True


def test_is_in_trading_session_false_at_close():
	# 16:00 is exclusive (half-open interval [09:30, 16:00))
	assert strategy.is_in_trading_session(_ny(16, 0)) is False


def test_is_in_trading_session_false_before_open():
	assert strategy.is_in_trading_session(_ny(9, 29)) is False


def test_is_in_trading_session_false_after_close():
	assert strategy.is_in_trading_session(_ny(16, 1)) is False


def test_is_in_trading_session_false_overnight():
	assert strategy.is_in_trading_session(_ny(2, 0)) is False


def test_is_in_trading_session_uses_current_time_when_now_is_none(monkeypatch):
	"""When now=None the function should call datetime.now(UTC) internally."""
	from zoneinfo import ZoneInfo

	# Freeze time to 11:00 ET (well within session)
	fixed = datetime(2026, 4, 26, 11, 0, tzinfo=ZoneInfo("America/New_York"))

	import strategy as _strat
	original_now = _strat.datetime.now  # type: ignore[attr-defined]

	# monkeypatch datetime.now inside the strategy module
	class _FakeDatetime(datetime):
		@classmethod
		def now(cls, tz=None):
			return fixed.astimezone(tz) if tz else fixed

	monkeypatch.setattr(_strat, "datetime", _FakeDatetime)
	result = _strat.is_in_trading_session(None)
	monkeypatch.setattr(_strat, "datetime", datetime)  # restore

	assert result is True
