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

	def send_message(self, msg, from_addr=None, to_addrs=None):
		"""Intercept send_message (used with MIMEText) and populate sendmail_args
		in the same format as sendmail() so existing test assertions keep working."""
		sender = from_addr or msg.get("From", "")
		to_header = msg.get("To", "")
		recipients = [addr.strip() for addr in to_header.split(",") if addr.strip()]
		payload = msg.get_payload(decode=True)
		if payload is not None:
			body = payload.decode(msg.get_content_charset("utf-8"))
		else:
			body = str(msg.get_payload())
		subject = msg.get("Subject", "")
		message_str = f"Subject: {subject}\n\n{body}"
		self.sendmail_args = (sender, recipients, message_str)


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
	assert "HIGH CONFIDENCE signal detected." in message
	assert "Direction:  BUY" in message
	assert "Timeframe:  M5" in message
	assert "Timestamp:  2026-04-15 11:00:00 UTC" in message
	assert "Entry:      39210.50" in message
	assert "Lot Size:   0.25" in message
	assert "SL:         39190.50" in message
	assert "TP:         39240.50" in message
	assert "RR:         1.50" in message
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


# ---------------------------------------------------------------------------
# send_bot_stopped_alert()
# ---------------------------------------------------------------------------

def test_send_bot_stopped_alert_sends_email_with_reason(monkeypatch):
	created = {}

	def fake_smtp(host, port):
		created["client"] = DummySMTP(host, port)
		return created["client"]

	monkeypatch.setattr(alerts.smtplib, "SMTP", fake_smtp)
	monkeypatch.setattr(alerts, "load_dotenv", lambda: None)
	monkeypatch.setattr(alerts.config, "ENABLE_EMAIL_ALERTS", True)
	monkeypatch.setenv("GMAIL_USER", "bot@example.com")
	monkeypatch.setenv("GMAIL_APP_PASSWORD", "app-password")
	monkeypatch.setattr(alerts.config, "EMAIL_RECIPIENT", ("receiver@example.com",))

	result = alerts.send_bot_stopped_alert("MT5 reconnect failed after all attempts.")

	assert result is True
	client = created["client"]
	assert client.started_tls is True
	assert client.login_args == ("bot@example.com", "app-password")
	assert client.sendmail_args is not None
	message = client.sendmail_args[2]
	assert "Subject: US30 Bot STOPPED" in message
	assert "MT5 reconnect failed after all attempts." in message
	assert "stopped automatically" in message


def test_send_bot_stopped_alert_returns_false_when_alerts_disabled(monkeypatch):
	monkeypatch.setattr(alerts.config, "ENABLE_EMAIL_ALERTS", False)

	result = alerts.send_bot_stopped_alert("some reason")

	assert result is False


def test_send_bot_stopped_alert_returns_false_when_credentials_missing(monkeypatch):
	monkeypatch.setattr(alerts, "load_dotenv", lambda: None)
	monkeypatch.setattr(alerts.config, "ENABLE_EMAIL_ALERTS", True)
	monkeypatch.delenv("GMAIL_USER", raising=False)
	monkeypatch.delenv("GMAIL_APP_PASSWORD", raising=False)

	result = alerts.send_bot_stopped_alert("some reason")

	assert result is False


def test_send_bot_stopped_alert_returns_false_when_no_recipients(monkeypatch):
	monkeypatch.setattr(alerts, "load_dotenv", lambda: None)
	monkeypatch.setattr(alerts.config, "ENABLE_EMAIL_ALERTS", True)
	monkeypatch.setenv("GMAIL_USER", "bot@example.com")
	monkeypatch.setenv("GMAIL_APP_PASSWORD", "app-password")
	monkeypatch.setattr(alerts.config, "EMAIL_RECIPIENT", [])

	result = alerts.send_bot_stopped_alert("some reason")

	assert result is False


def test_send_bot_stopped_alert_returns_false_on_smtp_error(monkeypatch):
	def bad_smtp(host, port):
		raise OSError("Connection refused")

	monkeypatch.setattr(alerts.smtplib, "SMTP", bad_smtp)
	monkeypatch.setattr(alerts, "load_dotenv", lambda: None)
	monkeypatch.setattr(alerts.config, "ENABLE_EMAIL_ALERTS", True)
	monkeypatch.setenv("GMAIL_USER", "bot@example.com")
	monkeypatch.setenv("GMAIL_APP_PASSWORD", "app-password")
	monkeypatch.setattr(alerts.config, "EMAIL_RECIPIENT", ("receiver@example.com",))

	result = alerts.send_bot_stopped_alert("MT5 reconnect failed.")

	assert result is False


# ---------------------------------------------------------------------------
# send_bot_started_alert()
# ---------------------------------------------------------------------------

def test_send_bot_started_alert_sends_email_with_account_details(monkeypatch):
	created = {}

	def fake_smtp(host, port):
		created["client"] = DummySMTP(host, port)
		return created["client"]

	monkeypatch.setattr(alerts.smtplib, "SMTP", fake_smtp)
	monkeypatch.setattr(alerts, "load_dotenv", lambda: None)
	monkeypatch.setattr(alerts.config, "ENABLE_EMAIL_ALERTS", True)
	monkeypatch.setenv("GMAIL_USER", "bot@example.com")
	monkeypatch.setenv("GMAIL_APP_PASSWORD", "app-password")
	monkeypatch.setattr(alerts.config, "EMAIL_RECIPIENT", ("receiver@example.com",))

	result = alerts.send_bot_started_alert(12345678, 1000.00, "Exness-Demo")

	assert result is True
	client = created["client"]
	assert client.started_tls is True
	message = client.sendmail_args[2]
	assert "Subject: US30 Bot STARTED" in message
	assert "12345678" in message
	assert "Exness-Demo" in message
	assert "1000.00" in message


def test_send_bot_started_alert_returns_false_when_alerts_disabled(monkeypatch):
	monkeypatch.setattr(alerts.config, "ENABLE_EMAIL_ALERTS", False)

	result = alerts.send_bot_started_alert(1, 500.0, "Demo")

	assert result is False


def test_send_bot_started_alert_returns_false_when_credentials_missing(monkeypatch):
	monkeypatch.setattr(alerts, "load_dotenv", lambda: None)
	monkeypatch.setattr(alerts.config, "ENABLE_EMAIL_ALERTS", True)
	monkeypatch.delenv("GMAIL_USER", raising=False)
	monkeypatch.delenv("GMAIL_APP_PASSWORD", raising=False)

	result = alerts.send_bot_started_alert(1, 500.0, "Demo")

	assert result is False


def test_send_bot_started_alert_returns_false_on_smtp_error(monkeypatch):
	def bad_smtp(host, port):
		raise OSError("Connection refused")

	monkeypatch.setattr(alerts.smtplib, "SMTP", bad_smtp)
	monkeypatch.setattr(alerts, "load_dotenv", lambda: None)
	monkeypatch.setattr(alerts.config, "ENABLE_EMAIL_ALERTS", True)
	monkeypatch.setenv("GMAIL_USER", "bot@example.com")
	monkeypatch.setenv("GMAIL_APP_PASSWORD", "app-password")
	monkeypatch.setattr(alerts.config, "EMAIL_RECIPIENT", ("receiver@example.com",))

	result = alerts.send_bot_started_alert(1, 500.0, "Demo")

	assert result is False


# ---------------------------------------------------------------------------
# send_no_signal_alert()
# ---------------------------------------------------------------------------

def test_send_no_signal_alert_sends_email_with_minutes(monkeypatch):
	created = {}

	def fake_smtp(host, port):
		created["client"] = DummySMTP(host, port)
		return created["client"]

	monkeypatch.setattr(alerts.smtplib, "SMTP", fake_smtp)
	monkeypatch.setattr(alerts, "load_dotenv", lambda: None)
	monkeypatch.setattr(alerts.config, "ENABLE_EMAIL_ALERTS", True)
	monkeypatch.setenv("GMAIL_USER", "bot@example.com")
	monkeypatch.setenv("GMAIL_APP_PASSWORD", "app-password")
	monkeypatch.setattr(alerts.config, "EMAIL_RECIPIENT", ("receiver@example.com",))

	result = alerts.send_no_signal_alert(30)

	assert result is True
	message = created["client"].sendmail_args[2]
	assert "Subject: US30 Bot - No Signal" in message
	assert "30 minute(s)" in message
	assert "still running" in message


def test_send_no_signal_alert_returns_false_when_alerts_disabled(monkeypatch):
	monkeypatch.setattr(alerts.config, "ENABLE_EMAIL_ALERTS", False)

	assert alerts.send_no_signal_alert(30) is False


# ---------------------------------------------------------------------------
# send_email_alert() — macro-FVG tier
# ---------------------------------------------------------------------------

def test_send_email_alert_sends_for_macro_fvg_signal(monkeypatch):
	"""send_email_alert fires for is_macro_fvg=True signals and includes FVG zone."""
	created = {}

	def fake_smtp(host, port):
		created["client"] = DummySMTP(host, port)
		return created["client"]

	monkeypatch.setattr(alerts.smtplib, "SMTP", fake_smtp)
	monkeypatch.setattr(alerts, "load_dotenv", lambda: None)
	monkeypatch.setattr(alerts.config, "ENABLE_EMAIL_ALERTS", True)
	monkeypatch.setenv("GMAIL_USER", "bot@example.com")
	monkeypatch.setenv("GMAIL_APP_PASSWORD", "app-password")
	monkeypatch.setattr(alerts.config, "EMAIL_RECIPIENT", ("receiver@example.com",))

	signal_dict = {
		"direction": "BUY",
		"timeframe": "M1",
		"entry_price": 77953.65,
		"is_macro_fvg": True,
		"fvg_bottom": 77853.49,
		"fvg_top": 77858.36,
		"liquidity_target": 78000.97,
	}
	risk_dict = {"lot_size": 0.01, "sl": 77833.49, "tp": 78000.97, "rr_ratio": 2.0}

	result = alerts.send_email_alert(signal_dict, risk_dict)

	assert result is True
	message = created["client"].sendmail_args[2]
	assert "Subject: US30 Signal Alert [MACRO FVG] - BUY (M1)" in message
	assert "MACRO FVG signal detected." in message
	assert "77853.49" in message
	assert "77858.36" in message
	assert "78000.97" in message


def test_send_email_alert_skips_when_none_of_the_flags_set(monkeypatch):
	"""Returns False when is_high_confidence, is_medium_confidence, and is_macro_fvg are all absent."""
	called = {"smtp": False}

	def fake_smtp(host, port):
		called["smtp"] = True
		return DummySMTP(host, port)

	monkeypatch.setattr(alerts.smtplib, "SMTP", fake_smtp)

	signal_dict = {"direction": "BUY", "timeframe": "M1", "entry_price": 77953.65}
	risk_dict = {"lot_size": 0.01, "sl": 77833.0, "tp": 78000.0, "rr_ratio": 1.5}

	result = alerts.send_email_alert(signal_dict, risk_dict)

	assert result is False
	assert called["smtp"] is False
