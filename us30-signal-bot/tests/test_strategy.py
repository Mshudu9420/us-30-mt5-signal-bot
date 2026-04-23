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
