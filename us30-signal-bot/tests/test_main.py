from types import SimpleNamespace
import os
import sys

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
	monkeypatch.setattr(main, "print_startup_summary", lambda account_info, cfg: called.update(summary=True))

	result = main.main()

	assert result is False
	assert called["summary"] is False


def test_main_returns_false_when_account_info_missing(monkeypatch, capsys):
	def fake_connect():
		return True

	def fake_account_info():
		return None

	monkeypatch.setattr(main, "connect", fake_connect)
	monkeypatch.setattr(main.mt5_connector.mt5, "account_info", fake_account_info)

	result = main.main()

	output = capsys.readouterr().out
	assert result is False
	assert "account info" in output.lower()