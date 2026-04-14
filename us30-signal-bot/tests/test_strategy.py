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
