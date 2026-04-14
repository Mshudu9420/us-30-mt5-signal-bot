import pandas as pd
import mt5_mock
import mt5_connector


def test_connect_success_prints_account_info(monkeypatch, capsys):
	monkeypatch.setattr(mt5_connector, "mt5", mt5_mock)
	mt5_mock.shutdown()

	connected = mt5_connector.connect()

	output = capsys.readouterr().out
	assert connected is True
	assert "MT5 connected" in output
	assert "login=" in output
	assert "server=" in output
	assert "balance=" in output


def test_connect_returns_false_when_initialize_fails(monkeypatch, capsys):
	class FailingMT5:
		@staticmethod
		def initialize():
			return False

		@staticmethod
		def last_error():
			return (100, "Init failed")

	monkeypatch.setattr(mt5_connector, "mt5", FailingMT5)

	connected = mt5_connector.connect()

	output = capsys.readouterr().out
	assert connected is False
	assert "MT5 initialization failed" in output


def test_disconnect_calls_shutdown_and_prints_message(monkeypatch, capsys):
	shutdown_called = []

	class TrackingMT5:
		@staticmethod
		def shutdown():
			shutdown_called.append(True)

	monkeypatch.setattr(mt5_connector, "mt5", TrackingMT5)

	mt5_connector.disconnect()

	output = capsys.readouterr().out
	assert shutdown_called, "mt5.shutdown() was not called"
	assert "MT5 disconnected" in output


def test_get_ohlcv_returns_dataframe_with_correct_shape(monkeypatch):
	monkeypatch.setattr(mt5_connector, "mt5", mt5_mock)
	mt5_mock.initialize()

	df = mt5_connector.get_ohlcv("US30", mt5_mock.TIMEFRAME_M5, 50)

	assert isinstance(df, pd.DataFrame)
	assert len(df) == 50


def test_get_ohlcv_dataframe_has_required_columns(monkeypatch):
	monkeypatch.setattr(mt5_connector, "mt5", mt5_mock)
	mt5_mock.initialize()

	df = mt5_connector.get_ohlcv("US30", mt5_mock.TIMEFRAME_M15, 10)

	for col in ("time", "open", "high", "low", "close", "tick_volume"):
		assert col in df.columns, f"Missing column: {col}"


def test_get_ohlcv_returns_none_when_no_data(monkeypatch):
	class EmptyMT5:
		@staticmethod
		def copy_rates_from_pos(symbol, timeframe, start, count):
			return []

	monkeypatch.setattr(mt5_connector, "mt5", EmptyMT5)

	result = mt5_connector.get_ohlcv("US30", 5, 50)

	assert result is None
