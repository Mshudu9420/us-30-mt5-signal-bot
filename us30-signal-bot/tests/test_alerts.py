import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import alerts


class DummySMTP:
	def __init__(self, host, port):
		self.host = host
		self.port = port
		self.started_tls = False
		self.login_args = None
		self.sendmail_args = None

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc, tb):
		return False

	def starttls(self):
		self.started_tls = True

	def login(self, user, password):
		self.login_args = (user, password)

	def sendmail(self, sender, recipients, message):
		self.sendmail_args = (sender, recipients, message)


def test_send_email_alert_sends_when_high_confidence(monkeypatch):
	created = {}
	dotenv_called = {"value": False}

	def fake_smtp(host, port):
		created["client"] = DummySMTP(host, port)
		return created["client"]

	def fake_load_dotenv():
		dotenv_called["value"] = True

	monkeypatch.setattr(alerts.smtplib, "SMTP", fake_smtp)
	monkeypatch.setattr(alerts, "load_dotenv", fake_load_dotenv)
	monkeypatch.setattr(alerts.config, "ENABLE_EMAIL_ALERTS", True)
	monkeypatch.setenv("GMAIL_USER", "bot@example.com")
	monkeypatch.setenv("GMAIL_APP_PASSWORD", "app-password")
	monkeypatch.setattr(alerts.config, "EMAIL_RECIPIENT", ("receiver@example.com",))

	signal_dict = {
		"direction": "BUY",
		"timeframe": "M5",
		"entry_price": 39210.5,
		"timestamp": "2026-04-15 11:00:00 UTC",
		"is_high_confidence": True,
	}
	risk_dict = {
		"lot_size": 0.25,
		"sl": 39190.5,
		"tp": 39240.5,
		"rr_ratio": 1.5,
	}

	result = alerts.send_email_alert(signal_dict, risk_dict)

	client = created["client"]
	assert result is True
	assert client.host == "smtp.gmail.com"
	assert client.port == 587
	assert client.started_tls is True
	assert client.login_args == ("bot@example.com", "app-password")
	assert client.sendmail_args is not None
	assert client.sendmail_args[0] == "bot@example.com"
	assert client.sendmail_args[1] == ["receiver@example.com"]
	message = client.sendmail_args[2]
	assert "Subject: US30 Signal Alert [HIGH CONFIDENCE] - BUY (M5)" in message
	assert "High-confidence US30 signal detected." in message
	assert "Direction: BUY" in message
	assert "Timeframe: M5" in message
	assert "Timestamp: 2026-04-15 11:00:00 UTC" in message
	assert "Entry: 39210.50" in message
	assert "Lot Size: 0.25" in message
	assert "SL: 39190.50" in message
	assert "TP: 39240.50" in message
	assert "RR: 1.50" in message
	assert dotenv_called["value"] is True


def test_send_email_alert_skips_when_not_high_confidence(monkeypatch):
	called = {"smtp": False}

	def fake_smtp(host, port):
		called["smtp"] = True
		return DummySMTP(host, port)

	monkeypatch.setattr(alerts.smtplib, "SMTP", fake_smtp)

	signal_dict = {
		"direction": "BUY",
		"timeframe": "M5",
		"entry_price": 39210.5,
		"timestamp": "2026-04-15 11:00:00 UTC",
		"is_high_confidence": False,
	}
	risk_dict = {
		"lot_size": 0.25,
		"sl": 39190.5,
		"tp": 39240.5,
		"rr_ratio": 1.5,
	}

	result = alerts.send_email_alert(signal_dict, risk_dict)

	assert result is False
	assert called["smtp"] is False
