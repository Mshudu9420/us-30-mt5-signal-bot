import pandas as pd

import indicators


def _build_price_df() -> pd.DataFrame:
	return pd.DataFrame(
		{
			"open": [9.5, 10.5, 11.5, 12.5, 13.5],
			"high": [10.5, 11.5, 12.5, 13.5, 14.5],
			"low": [9.0, 10.0, 11.0, 12.0, 13.0],
			"close": [10.0, 11.0, 12.0, 13.0, 14.0],
			"tick_volume": [100, 110, 120, 130, 140],
		}
	)


def test_calculate_bollinger_bands_adds_expected_columns():
	df = _build_price_df()

	result = indicators.calculate_bollinger_bands(df, period=3, std_dev=2)

	assert "bb_mid" in result.columns
	assert "bb_upper" in result.columns
	assert "bb_lower" in result.columns


def test_calculate_bollinger_bands_returns_expected_latest_values():
	df = _build_price_df()

	result = indicators.calculate_bollinger_bands(df, period=3, std_dev=2)
	latest = result.iloc[-1]

	assert round(latest["bb_mid"], 2) == 13.00
	assert round(latest["bb_upper"], 2) == 15.00
	assert round(latest["bb_lower"], 2) == 11.00


def test_calculate_rsi_adds_rsi_column():
	df = pd.DataFrame({"close": [10.0, 11.0, 12.0, 11.0, 12.0, 13.0]})

	result = indicators.calculate_rsi(df, period=3)

	assert "rsi" in result.columns


def test_calculate_rsi_returns_100_for_strict_uptrend_after_warmup():
	df = pd.DataFrame({"close": [10.0, 11.0, 12.0, 13.0, 14.0, 15.0]})

	result = indicators.calculate_rsi(df, period=3)

	assert round(result.iloc[-1]["rsi"], 2) == 100.00


def test_calculate_ema_adds_ema_column():
	df = _build_price_df()

	result = indicators.calculate_ema(df, period=3)

	assert "ema" in result.columns


# --- Fair Value Gap tests ---

def _build_fvg_df(rows: list[dict]) -> "pd.DataFrame":
	import pandas as pd
	return pd.DataFrame(rows)


def test_detect_fvg_finds_bullish_fvg():
	# bar[0].high=10 < bar[2].low=12 → bullish FVG, top=12, bottom=10
	df = _build_fvg_df([
		{"time": "2026-04-25 10:00", "open": 8, "high": 10, "low": 8, "close": 9},
		{"time": "2026-04-25 10:01", "open": 9, "high": 12, "low": 9, "close": 11},
		{"time": "2026-04-25 10:02", "open": 12, "high": 15, "low": 12, "close": 14},
	])

	result = indicators.detect_fvg(df)

	assert len(result) == 1
	assert result[0]["type"] == "bullish"
	assert result[0]["top"] == 12.0
	assert result[0]["bottom"] == 10.0
	assert result[0]["bar_index"] == 2


def test_detect_fvg_finds_bearish_fvg():
	# bar[0].low=12 > bar[2].high=11 → bearish FVG, top=12, bottom=11
	df = _build_fvg_df([
		{"time": "2026-04-25 10:00", "open": 15, "high": 16, "low": 12, "close": 13},
		{"time": "2026-04-25 10:01", "open": 13, "high": 14, "low": 10, "close": 11},
		{"time": "2026-04-25 10:02", "open": 11, "high": 11, "low": 8, "close": 9},
	])

	result = indicators.detect_fvg(df)

	assert len(result) == 1
	assert result[0]["type"] == "bearish"
	assert result[0]["top"] == 12.0
	assert result[0]["bottom"] == 11.0


def test_detect_fvg_returns_empty_when_no_gap():
	# Candles overlap — no FVG
	df = _build_fvg_df([
		{"time": "2026-04-25 10:00", "open": 10, "high": 11, "low": 9, "close": 10},
		{"time": "2026-04-25 10:01", "open": 10, "high": 12, "low": 9, "close": 11},
		{"time": "2026-04-25 10:02", "open": 11, "high": 12, "low": 10, "close": 11},
	])

	result = indicators.detect_fvg(df)

	assert result == []


def test_detect_fvg_attaches_time_of_third_candle():
	df = _build_fvg_df([
		{"time": "2026-04-25 10:00", "open": 8, "high": 10, "low": 8, "close": 9},
		{"time": "2026-04-25 10:01", "open": 9, "high": 12, "low": 9, "close": 11},
		{"time": "2026-04-25 10:02", "open": 12, "high": 15, "low": 12, "close": 14},
	])

	result = indicators.detect_fvg(df)

	assert result[0]["time"] == "2026-04-25 10:02"


# --- Nearest liquidity tests ---

def test_find_nearest_liquidity_returns_equal_highs_for_bullish():
	import pandas as pd
	# Two equal highs just above 100 → liquidity cluster ~105
	df = pd.DataFrame({
		"high": [105.0, 105.1, 90.0, 120.0],
		"low":  [95.0,  95.0,  85.0, 110.0],
	})

	result = indicators.find_nearest_liquidity(df, "BULLISH", reference_price=100.0, tolerance_pct=0.005)

	assert result is not None
	assert 104.0 < result < 106.0


def test_find_nearest_liquidity_returns_equal_lows_for_bearish():
	import pandas as pd
	# Two equal lows just below 100 → liquidity cluster ~95
	df = pd.DataFrame({
		"high": [105.0, 105.0, 110.0, 120.0],
		"low":  [95.0,  95.1,  85.0,  90.0],
	})

	result = indicators.find_nearest_liquidity(df, "BEARISH", reference_price=100.0, tolerance_pct=0.005)

	assert result is not None
	assert 94.0 < result < 96.0


def test_find_nearest_liquidity_returns_none_when_no_cluster():
	import pandas as pd
	# All highs are unique — no equal highs cluster
	df = pd.DataFrame({
		"high": [101.0, 102.0, 103.0, 104.0],
		"low":  [90.0,  91.0,  92.0,  93.0],
	})

	result = indicators.find_nearest_liquidity(df, "BULLISH", reference_price=100.0, tolerance_pct=0.001)

	assert result is None


def test_calculate_ema_returns_expected_latest_value():
	df = _build_price_df()

	result = indicators.calculate_ema(df, period=3)

	assert round(result.iloc[-1]["ema"], 2) == 13.06


def test_indicator_functions_return_dataframes_with_same_row_count():
	df = pd.DataFrame(
		{
			"open": [9.5, 10.5, 11.5, 12.5, 13.5, 14.5],
			"high": [10.5, 11.5, 12.5, 13.5, 14.5, 15.5],
			"low": [9.0, 10.0, 11.0, 12.0, 13.0, 14.0],
			"close": [10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
			"tick_volume": [100, 110, 120, 130, 140, 150],
		}
	)

	bb_result = indicators.calculate_bollinger_bands(df, period=3, std_dev=2)
	rsi_result = indicators.calculate_rsi(df, period=3)
	ema_result = indicators.calculate_ema(df, period=3)

	assert isinstance(bb_result, pd.DataFrame)
	assert isinstance(rsi_result, pd.DataFrame)
	assert isinstance(ema_result, pd.DataFrame)
	assert len(bb_result) == len(df)
	assert len(rsi_result) == len(df)
	assert len(ema_result) == len(df)


def test_get_latest_values_returns_latest_indicator_snapshot():
	df = _build_price_df()
	df = indicators.calculate_bollinger_bands(df, period=3, std_dev=2)
	df = indicators.calculate_rsi(df, period=3)
	df = indicators.calculate_ema(df, period=3)

	latest = indicators.get_latest_values(df)

	assert latest["close"] == 14.0
	assert round(latest["bb_mid"], 2) == 13.0
	assert round(latest["bb_upper"], 2) == 15.0
	assert round(latest["bb_lower"], 2) == 11.0
	assert round(latest["ema"], 2) == 13.06


def test_get_latest_values_includes_rsi_key():
	df = pd.DataFrame({"close": [10.0, 11.0, 12.0, 13.0, 14.0, 15.0]})
	df = indicators.calculate_rsi(df, period=3)

	latest = indicators.get_latest_values(df)

	assert "rsi" in latest
	assert round(latest["rsi"], 2) == 100.0


# --- MACD tests ---

def test_calculate_macd_adds_expected_columns():
	df = pd.DataFrame({"close": [float(i) for i in range(1, 51)]})

	result = indicators.calculate_macd(df, fast=3, slow=6, signal=3)

	assert "macd" in result.columns
	assert "macd_signal" in result.columns
	assert "macd_histogram" in result.columns


def test_calculate_macd_preserves_row_count():
	df = pd.DataFrame({"close": [float(i) for i in range(1, 51)]})

	result = indicators.calculate_macd(df, fast=3, slow=6, signal=3)

	assert len(result) == len(df)


def test_calculate_macd_histogram_is_macd_minus_signal():
	df = pd.DataFrame({"close": [float(i) for i in range(1, 51)]})

	result = indicators.calculate_macd(df, fast=3, slow=6, signal=3)

	for idx in result.index:
		h = result.loc[idx, "macd_histogram"]
		m = result.loc[idx, "macd"]
		s = result.loc[idx, "macd_signal"]
		if not (pd.isna(h) or pd.isna(m) or pd.isna(s)):
			assert abs(h - (m - s)) < 1e-9


def test_calculate_macd_histogram_rises_on_uptrend():
	# Steadily rising prices → fast EMA above slow EMA → histogram is positive
	df = pd.DataFrame({"close": [float(i) for i in range(1, 51)]})

	result = indicators.calculate_macd(df, fast=3, slow=6, signal=3)

	# Skip the first bar (0.0 before warm-up) and verify all remaining values are positive
	valid = result["macd_histogram"].dropna().iloc[1:]
	assert (valid > 0).all(), "Expected histogram to be positive on a steady uptrend"


def test_calculate_macd_histogram_falls_on_downtrend():
	# Steadily falling prices → fast EMA below slow EMA → histogram is negative
	df = pd.DataFrame({"close": [float(50 - i) for i in range(50)]})

	result = indicators.calculate_macd(df, fast=3, slow=6, signal=3)

	# Skip the first bar (0.0 before warm-up) and verify all remaining values are negative
	valid = result["macd_histogram"].dropna().iloc[1:]
	assert (valid < 0).all(), "Expected histogram to be negative on a steady downtrend"


def test_calculate_macd_does_not_modify_original_df():
	df = pd.DataFrame({"close": [float(i) for i in range(1, 21)]})
	orig_cols = set(df.columns)

	indicators.calculate_macd(df, fast=3, slow=6, signal=3)

	assert set(df.columns) == orig_cols
