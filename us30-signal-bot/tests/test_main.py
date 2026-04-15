from types import SimpleNamespace
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main


def test_main_initializes_and_prints_startup_summary(monkeypatch):
    called = {"summary": False}

    def fake_connect():
        return True

    def fake_account_info():
        return SimpleNamespace(login=12345678, server="Exness-Demo", balance=1000.0)

    def fake_summary(account_info, cfg):
        called["summary"] = True
        assert account_info.login == 12345678
        assert cfg.SYMBOL == "US30"

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
    assert mt5_mock.TIMEFRAME_M5 in fetch_calls
    assert mt5_mock.TIMEFRAME_M15 in fetch_calls
    assert mt5_mock.TIMEFRAME_H1 in fetch_calls
    assert len(heartbeat_calls) >= 1
