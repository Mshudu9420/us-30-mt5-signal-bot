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
