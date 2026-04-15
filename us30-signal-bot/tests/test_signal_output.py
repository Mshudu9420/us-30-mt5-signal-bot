from types import SimpleNamespace
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from signal_output import print_startup_summary


def test_print_startup_summary_outputs_settings_block(capsys):
	account_info = SimpleNamespace(
		login=12345678,
		server="Exness-Demo",
		balance=1000.0,
	)

	print_startup_summary(account_info, config)

	output = capsys.readouterr().out
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
	assert "OFF" in output
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