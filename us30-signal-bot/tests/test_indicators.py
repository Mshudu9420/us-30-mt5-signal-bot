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
