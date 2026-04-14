import pandas as pd
import mt5_mock
import mt5_connector
import config


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
	monkeypatch.setattr(mt5_connector.config, "MAX_RETRIES", 1)
	monkeypatch.setattr(mt5_connector.time, "sleep", lambda s: None)

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


def test_connect_retries_on_failure_and_succeeds(monkeypatch, capsys):
	"""Fails once then succeeds on second attempt."""
	attempts = [0]

	class FlakyMT5:
		@staticmethod
		def initialize():
			attempts[0] += 1
			return attempts[0] >= 2  # fail first, succeed second

		@staticmethod
		def last_error():
			return (100, "Transient error")

		@staticmethod
		def account_info():
			return mt5_mock.AccountInfo(login=99, server="Demo", balance=500.0)

	monkeypatch.setattr(mt5_connector, "mt5", FlakyMT5)
	monkeypatch.setattr(mt5_connector.config, "MAX_RETRIES", 3)
	monkeypatch.setattr(mt5_connector.config, "RETRY_DELAY_SECONDS", 0)
	monkeypatch.setattr(mt5_connector.time, "sleep", lambda s: None)

	result = mt5_connector.connect()

	output = capsys.readouterr().out
	assert result is True
	assert attempts[0] == 2
	assert "Retrying" in output
	assert "MT5 connected" in output


def test_connect_exhausts_retries_and_returns_false(monkeypatch, capsys):
	class AlwaysFailMT5:
		@staticmethod
		def initialize():
			return False

		@staticmethod
		def last_error():
			return (100, "Persistent error")

	monkeypatch.setattr(mt5_connector, "mt5", AlwaysFailMT5)
	monkeypatch.setattr(mt5_connector.config, "MAX_RETRIES", 3)
	monkeypatch.setattr(mt5_connector.config, "RETRY_DELAY_SECONDS", 0)
	monkeypatch.setattr(mt5_connector.time, "sleep", lambda s: None)

	result = mt5_connector.connect()

	output = capsys.readouterr().out
	assert result is False
	assert "max retries reached" in output


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


# --- mt5_mock.py integration tests (Task 2.6) ---

def test_disconnect_via_mock_resets_initialized_state(monkeypatch, capsys):
	"""disconnect() via mt5_mock leaves mock in uninitialized state."""
	monkeypatch.setattr(mt5_connector, "mt5", mt5_mock)
	mt5_mock.initialize()
	assert mt5_mock.account_info() is not None  # confirm connected

	mt5_connector.disconnect()

	assert mt5_mock.account_info() is None  # mock shut down


def test_get_ohlcv_returns_none_when_mock_not_initialized(monkeypatch):
	"""get_ohlcv() returns None when mt5_mock has not been initialized."""
	monkeypatch.setattr(mt5_connector, "mt5", mt5_mock)
	mt5_mock.shutdown()  # ensure uninitialized

	result = mt5_connector.get_ohlcv("US30", mt5_mock.TIMEFRAME_H1, 20)

	assert result is None


def test_get_ohlcv_time_column_is_utc_datetime(monkeypatch):
	"""time column in returned DataFrame must be timezone-aware datetime."""
	monkeypatch.setattr(mt5_connector, "mt5", mt5_mock)
	mt5_mock.initialize()

	df = mt5_connector.get_ohlcv("US30", mt5_mock.TIMEFRAME_H1, 5)

	assert pd.api.types.is_datetime64_any_dtype(df["time"])
	assert df["time"].dt.tz is not None
