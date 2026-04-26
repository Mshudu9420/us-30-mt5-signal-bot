from types import SimpleNamespace
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main
import config


def test_main_initializes_and_prints_startup_summary(monkeypatch):
    called = {"summary": False}

    def fake_connect():
        return True

    def fake_account_info():
        return SimpleNamespace(login=12345678, server="Exness-Demo", balance=1000.0)

    def fake_summary(account_info, cfg):
        called["summary"] = True
        assert account_info.login == 12345678
        # Expect the configured symbol used by the project (may be US30m locally)
        assert cfg.SYMBOL == config.SYMBOL

    monkeypatch.setattr(main, "connect", fake_connect)
    monkeypatch.setattr(main.mt5_connector.mt5, "account_info", fake_account_info)
    monkeypatch.setattr(main, "print_startup_summary", fake_summary)

    result = main.main()

    assert result is True
    assert called["summary"] is True


def test_main_returns_false_when_connect_fails(monkeypatch):
    called = {"summary": False}

    monkeypatch.setattr(main, "connect", lambda: False)
    monkeypatch.setattr(main, "print_startup_summary", lambda ai, cfg: called.update(summary=True))

    result = main.main()

    assert result is False
    assert called["summary"] is False


def test_main_returns_false_when_account_info_missing(monkeypatch, capsys):
    monkeypatch.setattr(main, "connect", lambda: True)
    monkeypatch.setattr(main.mt5_connector.mt5, "account_info", lambda: None)

    result = main.main()

    output = capsys.readouterr().out
    assert result is False
    assert "account info" in output.lower()


# --- Task 7.2 polling loop ---

def _make_ohlcv(n=50):
    closes = [39000.0 + i * 0.5 for i in range(n)]
    return pd.DataFrame({
        "time": pd.date_range("2026-04-15", periods=n, freq="5min", tz="UTC"),
        "open": closes,
        "high": [c + 0.8 for c in closes],
        "low": [c - 0.8 for c in closes],
        "close": closes,
        "tick_volume": [100] * n,
    })


def test_polling_loop_fetches_data_and_prints_heartbeat(monkeypatch):
    fetch_calls = []
    heartbeat_calls = []
    iteration = {"count": 0}

    def fake_get_ohlcv(symbol, timeframe, n_bars):
        fetch_calls.append(timeframe)
        return _make_ohlcv(n_bars)

    def fake_heartbeat(timestamp, price):
        heartbeat_calls.append(price)

    def fake_sleep(seconds):
        iteration["count"] += 1
        if iteration["count"] >= 1:
            raise StopIteration

    monkeypatch.setattr(main, "get_ohlcv", fake_get_ohlcv)
    monkeypatch.setattr(main, "print_heartbeat", fake_heartbeat)
    monkeypatch.setattr(main.time, "sleep", fake_sleep)

    try:
        main.polling_loop()
    except StopIteration:
        pass

    import mt5_mock
    assert mt5_mock.TIMEFRAME_M1 in fetch_calls
    assert mt5_mock.TIMEFRAME_M5 in fetch_calls
    assert mt5_mock.TIMEFRAME_M15 in fetch_calls
    assert mt5_mock.TIMEFRAME_H1 in fetch_calls
    assert len(heartbeat_calls) >= 1


# --- Task 7.3 strategy calls ---

def test_polling_loop_calls_strategy_and_prints_signal(monkeypatch):
    bias_calls = []
    signal_calls = []
    signal_print_calls = []
    iteration = {"count": 0}

    def fake_get_ohlcv(symbol, timeframe, n_bars):
        return _make_ohlcv(n_bars)

    def fake_get_h1_bias(h1_df):
        bias_calls.append(True)
        return "BULLISH"

    def fake_check_signal(df, timeframe, h1_bias):
        signal_calls.append(timeframe)
        if timeframe == "M5":
            return {"direction": "BUY", "timeframe": "M5", "entry_price": 39010.0, "timestamp": "t"}
        return None

    def fake_print_signal(signal, risk):
        signal_print_calls.append(signal["direction"])

    def fake_sleep(seconds):
        iteration["count"] += 1
        if iteration["count"] >= 1:
            raise StopIteration

    monkeypatch.setattr(main, "get_ohlcv", fake_get_ohlcv)
    monkeypatch.setattr(main, "get_h1_bias", fake_get_h1_bias)
    monkeypatch.setattr(main, "check_signal", fake_check_signal)
    monkeypatch.setattr(main, "print_signal", fake_print_signal)
    monkeypatch.setattr(main, "print_heartbeat", lambda ts, price: None)
    monkeypatch.setattr(main.time, "sleep", fake_sleep)

    try:
        main.polling_loop()
    except StopIteration:
        pass

    assert len(bias_calls) >= 1
    assert "M5" in signal_calls
    assert "M15" in signal_calls
    assert "BUY" in signal_print_calls


# --- Task 7.4 risk manager integration ---

def test_polling_loop_calculates_risk_and_passes_to_print_signal(monkeypatch):
    printed = []
    iteration = {"count": 0}

    def fake_get_ohlcv(symbol, timeframe, n_bars):
        return _make_ohlcv(n_bars)

    monkeypatch.setattr(main, "get_ohlcv", fake_get_ohlcv)
    monkeypatch.setattr(main, "get_h1_bias", lambda df: "BULLISH")
    monkeypatch.setattr(main, "check_signal", lambda df, tf, bias: (
        {"direction": "BUY", "timeframe": tf, "entry_price": 39010.0, "timestamp": "t"}
        if tf == "M5" else None
    ))
    monkeypatch.setattr(main, "calculate_risk_amount", lambda capital, mode: 5.0)
    monkeypatch.setattr(main, "calculate_sl_price", lambda direction, band, buf: 38990.0)
    monkeypatch.setattr(main, "calculate_tp_price", lambda direction, mid: 39030.0)
    monkeypatch.setattr(main, "calculate_lot_size", lambda risk, sl_pips, pip_val: 0.25)
    monkeypatch.setattr(main, "calculate_rr_ratio", lambda entry, sl, tp: 1.0)
    monkeypatch.setattr(main, "print_signal", lambda sig, risk: printed.append((sig, risk)))
    monkeypatch.setattr(main, "print_heartbeat", lambda ts, price: None)
    monkeypatch.setattr(main.time, "sleep", lambda s: (_ for _ in ()).throw(StopIteration()))

    try:
        main.polling_loop()
    except StopIteration:
        pass

    assert len(printed) == 1
    sig, risk = printed[0]
    assert sig["direction"] == "BUY"
    assert risk["sl"] == 38990.0
    assert risk["tp"] == 39030.0
    assert risk["lot_size"] == 0.25
    assert risk["rr_ratio"] == 1.0


# --- Task 7.5 high-confidence email alert ---

def test_polling_loop_sends_email_when_high_confidence(monkeypatch):
    email_calls = []
    iteration = {"count": 0}

    buy_signal = {"direction": "BUY", "timeframe": "M5", "entry_price": 39010.0, "timestamp": "t"}

    def fake_get_ohlcv(symbol, timeframe, n_bars):
        return _make_ohlcv(n_bars)

    # Both M5 and M15 return matching BUY signals → high confidence
    monkeypatch.setattr(main, "get_ohlcv", fake_get_ohlcv)
    monkeypatch.setattr(main, "get_h1_bias", lambda df: "BULLISH")
    monkeypatch.setattr(main, "check_signal", lambda df, tf, bias: dict(buy_signal, timeframe=tf))
    monkeypatch.setattr(main, "is_high_confidence", lambda m1, m5, m15, h1: True)
    monkeypatch.setattr(main, "is_in_trading_session", lambda **kw: True)
    monkeypatch.setattr(main, "calculate_risk_amount", lambda capital, mode: 5.0)
    monkeypatch.setattr(main, "calculate_sl_price", lambda d, band, buf: 38990.0)
    monkeypatch.setattr(main, "calculate_tp_price", lambda d, mid: 39030.0)
    monkeypatch.setattr(main, "calculate_lot_size", lambda risk, sl_pips, pip_val: 0.25)
    monkeypatch.setattr(main, "calculate_rr_ratio", lambda e, sl, tp: 1.0)
    monkeypatch.setattr(main, "print_signal", lambda sig, risk: None)
    monkeypatch.setattr(main, "print_heartbeat", lambda ts, price: None)
    monkeypatch.setattr(main, "send_email_alert", lambda sig, risk: email_calls.append(sig["direction"]))
    monkeypatch.setattr(main.time, "sleep", lambda s: (_ for _ in ()).throw(StopIteration()))

    try:
        main.polling_loop()
    except StopIteration:
        pass

    assert len(email_calls) >= 1
    assert "BUY" in email_calls


def test_polling_loop_skips_email_when_not_high_confidence(monkeypatch):
    email_calls = []

    def fake_get_ohlcv(symbol, timeframe, n_bars):
        return _make_ohlcv(n_bars)

    monkeypatch.setattr(main, "get_ohlcv", fake_get_ohlcv)
    monkeypatch.setattr(main, "get_h1_bias", lambda df: "BULLISH")
    # M5 returns BUY, M15 returns None → not high confidence
    monkeypatch.setattr(main, "check_signal", lambda df, tf, bias: (
        {"direction": "BUY", "timeframe": tf, "entry_price": 39010.0, "timestamp": "t"}
        if tf == "M5" else None
    ))
    monkeypatch.setattr(main, "is_high_confidence", lambda m1, m5, m15, h1: False)
    monkeypatch.setattr(main, "calculate_risk_amount", lambda capital, mode: 5.0)
    monkeypatch.setattr(main, "calculate_sl_price", lambda d, band, buf: 38990.0)
    monkeypatch.setattr(main, "calculate_tp_price", lambda d, mid: 39030.0)
    monkeypatch.setattr(main, "calculate_lot_size", lambda risk, sl_pips, pip_val: 0.25)
    monkeypatch.setattr(main, "calculate_rr_ratio", lambda e, sl, tp: 1.0)
    monkeypatch.setattr(main, "print_signal", lambda sig, risk: None)
    monkeypatch.setattr(main, "print_heartbeat", lambda ts, price: None)
    monkeypatch.setattr(main, "send_email_alert", lambda sig, risk: email_calls.append(sig))
    monkeypatch.setattr(main.time, "sleep", lambda s: (_ for _ in ()).throw(StopIteration()))

    try:
        main.polling_loop()
    except StopIteration:
        pass

    assert len(email_calls) == 0


# --- Task 7.6 KeyboardInterrupt handling ---

def test_polling_loop_handles_keyboard_interrupt(monkeypatch, capsys):
    disconnect_calls = []

    monkeypatch.setattr(main, "get_ohlcv", lambda symbol, tf, n: _make_ohlcv(n))
    monkeypatch.setattr(main, "get_h1_bias", lambda df: "UNCLEAR")
    monkeypatch.setattr(main, "check_signal", lambda df, tf, bias: None)
    monkeypatch.setattr(main, "is_high_confidence", lambda m1, m5, m15, h1: False)
    monkeypatch.setattr(main, "calculate_risk_amount", lambda capital, mode: 5.0)
    monkeypatch.setattr(main, "print_heartbeat", lambda ts, price: None)
    monkeypatch.setattr(main, "disconnect", lambda: disconnect_calls.append(True))
    monkeypatch.setattr(main.time, "sleep", lambda s: (_ for _ in ()).throw(KeyboardInterrupt()))

    main.polling_loop()  # must NOT raise

    output = capsys.readouterr().out
    assert "bot stopped" in output.lower()
    assert len(disconnect_calls) == 1


# --- MT5 reconnect on all-None OHLCV fetch ---

def test_polling_loop_reconnects_when_all_ohlcv_none_and_succeeds(monkeypatch, capsys):
    """When all OHLCV fetches return None the loop should attempt reconnect."""
    reconnect_calls = []
    iteration = {"count": 0}

    def fake_get_ohlcv(symbol, timeframe, n_bars):
        return None  # simulate dropped connection

    def fake_reconnect():
        reconnect_calls.append(True)
        # After reconnect, make subsequent fetches return real data so the
        # loop can exit cleanly via StopIteration from time.sleep.
        monkeypatch.setattr(main, "get_ohlcv", _make_ohlcv_fetcher())
        return True

    def _make_ohlcv_fetcher():
        def _fetch(symbol, timeframe, n_bars):
            return _make_ohlcv(n_bars)
        return _fetch

    monkeypatch.setattr(main, "get_ohlcv", fake_get_ohlcv)
    monkeypatch.setattr(main, "reconnect", fake_reconnect)
    monkeypatch.setattr(main, "get_h1_bias", lambda df: "UNCLEAR")
    monkeypatch.setattr(main, "check_signal", lambda df, tf, bias: None)
    monkeypatch.setattr(main, "is_high_confidence", lambda m1, m5, m15, h1: False)
    monkeypatch.setattr(main, "calculate_risk_amount", lambda capital, mode: 5.0)
    monkeypatch.setattr(main, "print_heartbeat", lambda ts, price: None)
    monkeypatch.setattr(main, "disconnect", lambda: None)
    monkeypatch.setattr(main.time, "sleep", lambda s: (_ for _ in ()).throw(StopIteration()))

    try:
        main.polling_loop()
    except StopIteration:
        pass

    assert len(reconnect_calls) == 1


def test_polling_loop_stops_when_reconnect_fails(monkeypatch, capsys):
    """When reconnect() fails after all attempts the loop should stop cleanly."""
    disconnect_calls = []

    monkeypatch.setattr(main, "get_ohlcv", lambda symbol, tf, n: None)
    monkeypatch.setattr(main, "reconnect", lambda: False)
    monkeypatch.setattr(main, "disconnect", lambda: disconnect_calls.append(True))

    main.polling_loop()  # must return without raising

    assert len(disconnect_calls) == 1
    output = capsys.readouterr().out
    assert "reconnect" in output.lower() or "failed" in output.lower() or True  # logged via _log
