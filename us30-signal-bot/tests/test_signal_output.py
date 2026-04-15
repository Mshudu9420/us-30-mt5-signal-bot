from types import SimpleNamespace
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from signal_output import print_heartbeat, print_signal, print_startup_summary


def test_print_startup_summary_outputs_settings_block(capsys):
	account_info = SimpleNamespace(
		login=12345678,
		server="Exness-Demo",
		balance=1000.0,
	)

	print_startup_summary(account_info, config)

	output = capsys.readouterr().out
	email_status = "ON" if config.ENABLE_EMAIL_ALERTS else "OFF"
	assert "US30 MT5 SIGNAL BOT" in output
	assert "BROKER" in output
	assert "Exness" in output
	assert "SYMBOL" in output
	assert "US30" in output
	assert "RISK MODE" in output
	assert "conservative" in output
	assert "ENTRY TIMEFRAMES" in output
	assert "M5, M15" in output
	assert "BIAS TIMEFRAME" in output
	assert "H1" in output
	assert "POLL INTERVAL" in output
	assert "60s" in output
	assert "EMAIL ALERTS" in output
	assert email_status in output
	assert "ACCOUNT LOGIN" in output
	assert "12345678" in output
	assert "ACCOUNT SERVER" in output
	assert "Exness-Demo" in output
	assert "ACCOUNT BALANCE" in output
	assert "1000.00" in output


def test_print_startup_summary_uses_colorama_formatting(capsys):
	account_info = SimpleNamespace(
		login=12345678,
		server="Exness-Demo",
		balance=1000.0,
	)

	print_startup_summary(account_info, config)

	output = capsys.readouterr().out
	assert "\x1b[" in output


def test_print_heartbeat_outputs_timestamp_and_price(capsys):
	print_heartbeat("2026-04-15 10:30:00 UTC", 39210.5)

	output = capsys.readouterr().out.strip()
	assert "2026-04-15 10:30:00 UTC" in output
	assert "39210.50" in output
	assert "heartbeat" in output.lower()


def test_print_heartbeat_uses_low_prominence_formatting(capsys):
	print_heartbeat("2026-04-15 10:30:00 UTC", 39210.5)

	output = capsys.readouterr().out
	assert "\x1b[" in output


def test_print_signal_outputs_block_with_risk_fields(capsys):
	signal_dict = {
		"direction": "BUY",
		"timeframe": "M5",
		"entry_price": 39210.50,
		"timestamp": "2026-04-15 10:35:00 UTC",
	}
	risk_dict = {
		"lot_size": 0.25,
		"sl": 39190.50,
		"tp": 39240.50,
		"rr_ratio": 1.50,
	}

	print_signal(signal_dict, risk_dict)

	output = capsys.readouterr().out
	assert "-" * 60 in output
	assert "SIGNAL" in output
	assert "BUY" in output
	assert "TIMEFRAME" in output
	assert "M5" in output
	assert "ENTRY" in output
	assert "39210.50" in output
	assert "LOT SIZE" in output
	assert "0.25" in output
	assert "SL" in output
	assert "39190.50" in output
	assert "TP" in output
	assert "39240.50" in output
	assert "RR" in output
	assert "1.50" in output


def test_print_signal_colors_direction(capsys):
	buy_signal = {
		"direction": "BUY",
		"timeframe": "M5",
		"entry_price": 39210.50,
		"timestamp": "2026-04-15 10:35:00 UTC",
	}
	risk_dict = {
		"lot_size": 0.25,
		"sl": 39190.50,
		"tp": 39240.50,
		"rr_ratio": 1.50,
	}

	print_signal(buy_signal, risk_dict)
	buy_output = capsys.readouterr().out

	sell_signal = dict(buy_signal)
	sell_signal["direction"] = "SELL"
	print_signal(sell_signal, risk_dict)
	sell_output = capsys.readouterr().out

	assert "\x1b[" in buy_output
	assert "\x1b[" in sell_output