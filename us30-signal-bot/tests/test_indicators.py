import pandas as pd

import indicators


def _build_price_df() -> pd.DataFrame:
	return pd.DataFrame(
		{
			"close": [10.0, 11.0, 12.0, 13.0, 14.0],
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
