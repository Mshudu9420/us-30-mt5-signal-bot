import types

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

	df = mt5_connector.get_ohlcv(config.SYMBOL, mt5_mock.TIMEFRAME_M5, 50)

	assert isinstance(df, pd.DataFrame)
	assert len(df) == 50


def test_get_ohlcv_dataframe_has_required_columns(monkeypatch):
	monkeypatch.setattr(mt5_connector, "mt5", mt5_mock)
	mt5_mock.initialize()

	df = mt5_connector.get_ohlcv(config.SYMBOL, mt5_mock.TIMEFRAME_M15, 10)

	for col in ("time", "open", "high", "low", "close", "tick_volume"):
		assert col in df.columns, f"Missing column: {col}"


def test_get_ohlcv_returns_none_when_no_data(monkeypatch):
	class EmptyMT5:
		@staticmethod
		def copy_rates_from_pos(symbol, timeframe, start, count):
			return []

	monkeypatch.setattr(mt5_connector, "mt5", EmptyMT5)

	result = mt5_connector.get_ohlcv(config.SYMBOL, 5, 50)

	assert result is None


def test_get_ohlcv_uses_fallback_symbol_when_primary_has_no_data(monkeypatch):
	calls = []

	class FallbackMT5:
		@staticmethod
		def copy_rates_from_pos(symbol, timeframe, start, count):
			calls.append(symbol)
			if symbol == config.SYMBOL:
				return []
			if symbol == "US30.cash":
				return [{
					"time": 1710000000,
					"open": 1.0,
					"high": 1.0,
					"low": 1.0,
					"close": 1.0,
					"tick_volume": 1,
					"spread": 0,
					"real_volume": 1,
				}]
			return []

	monkeypatch.setattr(mt5_connector, "mt5", FallbackMT5)
	monkeypatch.setattr(mt5_connector.config, "SYMBOL_FALLBACKS", ["US30.cash", "DJIA"])

	df = mt5_connector.get_ohlcv(config.SYMBOL, 5, 50)

	assert df is not None
	assert calls[:2] == [config.SYMBOL, "US30.cash"]


def test_get_ohlcv_stops_after_primary_symbol_success(monkeypatch):
	calls = []

	class PrimaryWinsMT5:
		@staticmethod
		def copy_rates_from_pos(symbol, timeframe, start, count):
			calls.append(symbol)
			if symbol == config.SYMBOL:
				return [{
					"time": 1710000000,
					"open": 1.0,
					"high": 1.0,
					"low": 1.0,
					"close": 1.0,
					"tick_volume": 1,
					"spread": 0,
					"real_volume": 1,
				}]
			return []

	monkeypatch.setattr(mt5_connector, "mt5", PrimaryWinsMT5)
	monkeypatch.setattr(mt5_connector.config, "SYMBOL_FALLBACKS", ["US30.cash", "DJIA"])

	df = mt5_connector.get_ohlcv(config.SYMBOL, 5, 50)

	assert df is not None
	assert calls == [config.SYMBOL]


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

	result = mt5_connector.get_ohlcv(config.SYMBOL, mt5_mock.TIMEFRAME_H1, 20)

	assert result is None


def test_get_ohlcv_time_column_is_utc_datetime(monkeypatch):
	"""time column in returned DataFrame must be timezone-aware datetime."""
	monkeypatch.setattr(mt5_connector, "mt5", mt5_mock)
	mt5_mock.initialize()

	df = mt5_connector.get_ohlcv(config.SYMBOL, mt5_mock.TIMEFRAME_H1, 5)

	assert pd.api.types.is_datetime64_any_dtype(df["time"])
	assert df["time"].dt.tz is not None


# --- has_open_position tests ---

def test_has_open_position_returns_false_when_no_positions(monkeypatch):
	"""Returns False when positions_get returns an empty list."""
	class NoPositionsMT5:
		@staticmethod
		def positions_get(symbol=None):
			return []

	monkeypatch.setattr(mt5_connector, "mt5", NoPositionsMT5)

	assert mt5_connector.has_open_position("BTCUSDm", "BUY") is False
	assert mt5_connector.has_open_position("BTCUSDm", "SELL") is False


def test_has_open_position_returns_true_for_matching_buy(monkeypatch):
	"""Returns True when a BUY position (type=0) already exists."""
	class FakePosition:
		type = 0  # MT5 BUY

	class WithBuyMT5:
		@staticmethod
		def positions_get(symbol=None):
			return [FakePosition()]

	monkeypatch.setattr(mt5_connector, "mt5", WithBuyMT5)

	assert mt5_connector.has_open_position("BTCUSDm", "BUY") is True
	assert mt5_connector.has_open_position("BTCUSDm", "SELL") is False


def test_has_open_position_returns_true_for_matching_sell(monkeypatch):
	"""Returns True when a SELL position (type=1) already exists."""
	class FakePosition:
		type = 1  # MT5 SELL

	class WithSellMT5:
		@staticmethod
		def positions_get(symbol=None):
			return [FakePosition()]

	monkeypatch.setattr(mt5_connector, "mt5", WithSellMT5)

	assert mt5_connector.has_open_position("BTCUSDm", "SELL") is True
	assert mt5_connector.has_open_position("BTCUSDm", "BUY") is False


def test_has_open_position_returns_false_when_positions_get_missing(monkeypatch):
	"""Returns False gracefully when positions_get is not available."""
	class NoAttrMT5:
		pass  # no positions_get attribute

	monkeypatch.setattr(mt5_connector, "mt5", NoAttrMT5)

	assert mt5_connector.has_open_position("BTCUSDm", "BUY") is False


def test_has_open_position_returns_false_when_positions_get_raises(monkeypatch):
	"""Returns False when positions_get raises an unexpected exception."""
	class BrokenMT5:
		@staticmethod
		def positions_get(symbol=None):
			raise RuntimeError("MT5 error")

	monkeypatch.setattr(mt5_connector, "mt5", BrokenMT5)

	assert mt5_connector.has_open_position("BTCUSDm", "BUY") is False


# ---------------------------------------------------------------------------
# reconnect()
# ---------------------------------------------------------------------------

def test_reconnect_returns_true_on_first_attempt(monkeypatch, capsys):
	"""Reconnect should succeed immediately when connect() works on first try."""
	shutdown_calls = []

	class QuickMT5:
		@staticmethod
		def shutdown():
			shutdown_calls.append(True)

		@staticmethod
		def initialize():
			return True

		@staticmethod
		def account_info():
			return mt5_mock.AccountInfo(login=1, server="Demo", balance=1000.0)

	monkeypatch.setattr(mt5_connector, "mt5", QuickMT5)
	monkeypatch.setattr(mt5_connector.time, "sleep", lambda s: None)

	result = mt5_connector.reconnect(max_attempts=3, backoff_base=0)

	assert result is True
	assert shutdown_calls, "mt5.shutdown() should be called before reconnecting"
	output = capsys.readouterr().out
	assert "reconnected" in output.lower()


def test_reconnect_retries_with_backoff_and_succeeds(monkeypatch, capsys):
	"""Fails twice then succeeds on the third attempt."""
	attempts = [0]
	sleep_calls = []

	class FlakyMT5:
		@staticmethod
		def shutdown():
			pass

		@staticmethod
		def initialize():
			attempts[0] += 1
			return attempts[0] >= 3

		@staticmethod
		def last_error():
			return (1, "transient")

		@staticmethod
		def account_info():
			return mt5_mock.AccountInfo(login=1, server="Demo", balance=1000.0)

	monkeypatch.setattr(mt5_connector, "mt5", FlakyMT5)
	monkeypatch.setattr(mt5_connector.time, "sleep", lambda s: sleep_calls.append(s))
	monkeypatch.setattr(mt5_connector.config, "MAX_RETRIES", 1)
	monkeypatch.setattr(mt5_connector.config, "RETRY_DELAY_SECONDS", 0)

	result = mt5_connector.reconnect(max_attempts=5, backoff_base=1)

	assert result is True
	# Two failed attempts → two backoff sleeps before the third succeeds
	assert len(sleep_calls) == 2
	# Backoff doubles: first=1s, second=2s
	assert sleep_calls[0] == 1.0
	assert sleep_calls[1] == 2.0


def test_reconnect_returns_false_when_all_attempts_exhausted(monkeypatch, capsys):
	"""Returns False and logs failure when every attempt fails."""
	class AlwaysFailMT5:
		@staticmethod
		def shutdown():
			pass

		@staticmethod
		def initialize():
			return False

		@staticmethod
		def last_error():
			return (1, "down")

	monkeypatch.setattr(mt5_connector, "mt5", AlwaysFailMT5)
	monkeypatch.setattr(mt5_connector.time, "sleep", lambda s: None)
	monkeypatch.setattr(mt5_connector.config, "MAX_RETRIES", 1)
	monkeypatch.setattr(mt5_connector.config, "RETRY_DELAY_SECONDS", 0)

	result = mt5_connector.reconnect(max_attempts=3, backoff_base=0)

	assert result is False
	output = capsys.readouterr().out
	assert "exhausted" in output.lower() or "failed" in output.lower()


# ---------------------------------------------------------------------------
# place_market_order()
# ---------------------------------------------------------------------------

def _make_order_mt5(*, fail_tick=False, raise_on_send=False, include_filling=True):
	"""Return a minimal MT5 stub suitable for place_market_order tests."""

	class FakeTick:
		ask = 78500.0
		bid = 78490.0

	class _MT5:
		ORDER_TYPE_BUY = 0
		ORDER_TYPE_SELL = 1
		TRADE_ACTION_DEAL = 1
		if include_filling:
			ORDER_TIME_GTC = 1
			ORDER_FILLING_FOK = 3

		@staticmethod
		def symbol_info_tick(symbol):
			return None if fail_tick else FakeTick()

		@staticmethod
		def order_send(request):
			if raise_on_send:
				raise RuntimeError("MT5 terminal disconnected")
			return types.SimpleNamespace(retcode=10009, order=123456)

	return _MT5


def test_place_market_order_returns_failure_when_no_order_send(monkeypatch):
	"""Returns failure dict when mt5 has no order_send attribute."""

	class NoOrderSendMT5:
		pass  # no order_send

	monkeypatch.setattr(mt5_connector, "mt5", NoOrderSendMT5)

	result = mt5_connector.place_market_order("BTCUSDm", "BUY", 0.01)

	assert result["success"] is False
	assert "order_send" in result["error"]


def test_place_market_order_returns_failure_when_tick_unavailable(monkeypatch):
	"""Returns failure dict when symbol_info_tick returns None."""
	monkeypatch.setattr(mt5_connector, "mt5", _make_order_mt5(fail_tick=True))

	result = mt5_connector.place_market_order("BTCUSDm", "BUY", 0.01)

	assert result["success"] is False
	assert "tick info unavailable" in result["error"]
	assert "BTCUSDm" in result["error"]


def test_place_market_order_buy_uses_ask_price(monkeypatch):
	"""BUY order puts tick.ask into the request and sets ORDER_TYPE_BUY."""
	requests_sent = []

	_MT5 = _make_order_mt5()

	def capturing_send(request):
		requests_sent.append(request)
		return types.SimpleNamespace(retcode=10009, order=123456)

	_MT5.order_send = staticmethod(capturing_send)
	monkeypatch.setattr(mt5_connector, "mt5", _MT5)

	result = mt5_connector.place_market_order(
		"BTCUSDm", "BUY", 0.01, sl=78400.0, tp=78600.0
	)

	assert result["success"] is True
	req = requests_sent[0]
	assert req["price"] == 78500.0
	assert req["type"] == 0  # ORDER_TYPE_BUY
	assert req["volume"] == 0.01
	assert req["sl"] == 78400.0
	assert req["tp"] == 78600.0
	assert req["comment"] == "us30-signal-bot"


def test_place_market_order_sell_uses_bid_price(monkeypatch):
	"""SELL order puts tick.bid into the request and sets ORDER_TYPE_SELL."""
	requests_sent = []

	_MT5 = _make_order_mt5()

	def capturing_send(request):
		requests_sent.append(request)
		return types.SimpleNamespace(retcode=10009, order=654321)

	_MT5.order_send = staticmethod(capturing_send)
	monkeypatch.setattr(mt5_connector, "mt5", _MT5)

	result = mt5_connector.place_market_order("BTCUSDm", "SELL", 0.05)

	assert result["success"] is True
	req = requests_sent[0]
	assert req["price"] == 78490.0
	assert req["type"] == 1  # ORDER_TYPE_SELL
	assert req["volume"] == 0.05


def test_place_market_order_sl_tp_default_to_zero_when_omitted(monkeypatch):
	"""sl and tp are 0.0 in the request when not provided."""
	requests_sent = []

	_MT5 = _make_order_mt5()

	def capturing_send(request):
		requests_sent.append(request)
		return types.SimpleNamespace(retcode=10009, order=1)

	_MT5.order_send = staticmethod(capturing_send)
	monkeypatch.setattr(mt5_connector, "mt5", _MT5)

	mt5_connector.place_market_order("BTCUSDm", "BUY", 0.01)

	assert requests_sent[0]["sl"] == 0.0
	assert requests_sent[0]["tp"] == 0.0


def test_place_market_order_uses_config_defaults_for_deviation_and_magic(monkeypatch):
	"""ORDER_DEVIATION and ORDER_MAGIC from config flow into the request."""
	requests_sent = []

	_MT5 = _make_order_mt5()

	def capturing_send(request):
		requests_sent.append(request)
		return types.SimpleNamespace(retcode=10009, order=1)

	_MT5.order_send = staticmethod(capturing_send)
	monkeypatch.setattr(mt5_connector, "mt5", _MT5)
	monkeypatch.setattr(mt5_connector.config, "ORDER_DEVIATION", 15)
	monkeypatch.setattr(mt5_connector.config, "ORDER_MAGIC", 42)

	mt5_connector.place_market_order("BTCUSDm", "BUY", 0.01)

	assert requests_sent[0]["deviation"] == 15
	assert requests_sent[0]["magic"] == 42


def test_place_market_order_explicit_deviation_and_magic_override_config(monkeypatch):
	"""Caller-provided deviation/magic override config values."""
	requests_sent = []

	_MT5 = _make_order_mt5()

	def capturing_send(request):
		requests_sent.append(request)
		return types.SimpleNamespace(retcode=10009, order=1)

	_MT5.order_send = staticmethod(capturing_send)
	monkeypatch.setattr(mt5_connector, "mt5", _MT5)
	monkeypatch.setattr(mt5_connector.config, "ORDER_DEVIATION", 20)
	monkeypatch.setattr(mt5_connector.config, "ORDER_MAGIC", 0)

	mt5_connector.place_market_order("BTCUSDm", "BUY", 0.01, deviation=5, magic=99)

	assert requests_sent[0]["deviation"] == 5
	assert requests_sent[0]["magic"] == 99


def test_place_market_order_includes_filling_and_time_when_available(monkeypatch):
	"""ORDER_TIME_GTC and ORDER_FILLING_FOK are added when the mt5 stub exposes them."""
	requests_sent = []

	_MT5 = _make_order_mt5(include_filling=True)

	def capturing_send(request):
		requests_sent.append(request)
		return types.SimpleNamespace(retcode=10009, order=1)

	_MT5.order_send = staticmethod(capturing_send)
	monkeypatch.setattr(mt5_connector, "mt5", _MT5)

	mt5_connector.place_market_order("BTCUSDm", "BUY", 0.01)

	assert "type_time" in requests_sent[0]
	assert "type_filling" in requests_sent[0]


def test_place_market_order_omits_filling_when_unavailable(monkeypatch):
	"""type_time / type_filling are absent when mt5 stub lacks those constants."""
	requests_sent = []

	_MT5 = _make_order_mt5(include_filling=False)

	def capturing_send(request):
		requests_sent.append(request)
		return types.SimpleNamespace(retcode=10009, order=1)

	_MT5.order_send = staticmethod(capturing_send)
	monkeypatch.setattr(mt5_connector, "mt5", _MT5)

	mt5_connector.place_market_order("BTCUSDm", "BUY", 0.01)

	assert "type_time" not in requests_sent[0]
	assert "type_filling" not in requests_sent[0]


def test_place_market_order_returns_failure_when_order_send_raises(monkeypatch):
	"""Returns failure dict when order_send raises an unexpected exception."""
	monkeypatch.setattr(mt5_connector, "mt5", _make_order_mt5(raise_on_send=True))

	result = mt5_connector.place_market_order("BTCUSDm", "BUY", 0.01)

	assert result["success"] is False
	assert "MT5 terminal disconnected" in result["error"]


def test_place_market_order_returns_retcode_in_success_result(monkeypatch):
	"""Successful response includes retcode extracted from the MT5 result object."""
	monkeypatch.setattr(mt5_connector, "mt5", _make_order_mt5())

	result = mt5_connector.place_market_order("BTCUSDm", "BUY", 0.01)

	assert result["success"] is True
	assert result["retcode"] == 10009


# ---------------------------------------------------------------------------
# summarize_order_result()
# ---------------------------------------------------------------------------

def test_summarize_order_result_returns_failure_summary_for_failed_response():
	response = {"success": False, "error": "symbol tick info unavailable for BTCUSDm"}

	summary = mt5_connector.summarize_order_result(response)

	assert summary == {"success": False, "error": "symbol tick info unavailable for BTCUSDm"}


def test_summarize_order_result_extracts_retcode_and_order_id():
	result_obj = types.SimpleNamespace(retcode=10009, order=99876)
	response = {"success": True, "result": result_obj, "retcode": 10009}

	summary = mt5_connector.summarize_order_result(response)

	assert summary["success"] is True
	assert summary["retcode"] == 10009
	assert summary["order_id"] == 99876


def test_summarize_order_result_handles_missing_order_id_gracefully():
	result_obj = types.SimpleNamespace()  # no order attribute
	response = {"success": True, "result": result_obj, "retcode": 10009}

	summary = mt5_connector.summarize_order_result(response)

	assert summary["success"] is True
	assert "order_id" not in summary


def test_summarize_order_result_extracts_volume_and_price_from_request_dict():
	req = {"volume": 0.05, "price": 78500.0}
	result_obj = types.SimpleNamespace(request=req, order=1)
	response = {"success": True, "result": result_obj, "retcode": 10009}

	summary = mt5_connector.summarize_order_result(response)

	assert summary["volume"] == 0.05
	assert summary["price"] == 78500.0


def test_summarize_order_result_success_false_when_key_absent():
	"""Treats missing 'success' key as failure."""
	response = {"error": "something went wrong"}

	summary = mt5_connector.summarize_order_result(response)

	assert summary["success"] is False
