"""Email alert helpers for high-confidence trading signals."""

import os
import smtplib
from dotenv import load_dotenv

import config


def _normalize_recipients(recipients_value):
	"""Normalize recipients into a list of non-empty email strings."""
	if isinstance(recipients_value, (tuple, list)):
		return [str(r).strip() for r in recipients_value if str(r).strip()]
	if isinstance(recipients_value, str):
		return [r.strip() for r in recipients_value.split(",") if r.strip()]
	return []


def send_email_alert(signal_dict, risk_dict) -> bool:
	"""Send a Gmail SMTP alert for high-confidence or medium-confidence signals."""
	is_high = signal_dict.get("is_high_confidence", False)
	is_medium = signal_dict.get("is_medium_confidence", False)
	if not is_high and not is_medium:
		return False

	if not config.ENABLE_EMAIL_ALERTS:
		return False

	# Load runtime secrets (GMAIL_USER/GMAIL_APP_PASSWORD) from .env if present.
	load_dotenv()

	gmail_user = os.getenv("GMAIL_USER")
	gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")
	if not gmail_user or not gmail_app_password:
		return False

	recipients = _normalize_recipients(config.EMAIL_RECIPIENT)
	if not recipients:
		return False

	direction = signal_dict.get("direction", "UNKNOWN")
	timeframe = signal_dict.get("timeframe", "-")
	timestamp = signal_dict.get("timestamp", "-")
	entry_price = float(signal_dict.get("entry_price", 0.0))
	lot_size = float(risk_dict.get("lot_size", 0.0))
	sl = float(risk_dict.get("sl", 0.0))
	tp = float(risk_dict.get("tp", 0.0))
	rr_ratio = float(risk_dict.get("rr_ratio", 0.0))

	tier = "HIGH CONFIDENCE" if is_high else "MEDIUM CONFIDENCE"
	subject = f"US30 Signal Alert [{tier}] - {direction} ({timeframe})"
	body = (
		f"{tier} signal detected.\n\n"
		f"Direction:  {direction}\n"
		f"Timeframe:  {timeframe}\n"
		f"Timestamp:  {timestamp}\n"
		f"Entry:      {entry_price:.2f}\n"
		f"Lot Size:   {lot_size:.2f}\n"
		f"SL:         {sl:.2f}\n"
		f"TP:         {tp:.2f}\n"
		f"RR:         {rr_ratio:.2f}\n"
	)

	message = f"Subject: {subject}\n\n{body}"

	# Append order info / summary to the email body if the signal includes it
	order_info = signal_dict.get("order_info")
	if order_info is not None:
		message += f"\nORDER INFO (raw):\n{order_info}\n"

	order_summary = signal_dict.get("order_summary")
	if order_summary is not None:
		# order_summary is expected to be a dict; format key: value lines for readability
		message += "\nORDER SUMMARY:\n"
		if isinstance(order_summary, dict):
			for k, v in order_summary.items():
				message += f"- {k}: {v}\n"
		else:
			message += f"{order_summary}\n"

	# The bot only supports Gmail SMTP for sending alerts.
	# Use smtp.gmail.com with STARTTLS on port 587 and optional DEBUG_SMTP.
	with smtplib.SMTP("smtp.gmail.com", 587) as server:
		if os.getenv("DEBUG_SMTP", "").lower() in ("1", "true", "yes"):
			server.set_debuglevel(1)
		server.starttls()
		server.login(gmail_user, gmail_app_password)
		server.sendmail(gmail_user, recipients, message)

	return True


def _smtp_send(subject: str, body: str) -> bool:
	"""Shared helper: authenticate and send a single plain-text email.

	Returns True on success, False if alerts are disabled, credentials are
	missing, recipients list is empty, or an SMTP error occurs.
	"""
	if not config.ENABLE_EMAIL_ALERTS:
		return False

	load_dotenv()

	gmail_user = os.getenv("GMAIL_USER")
	gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")
	if not gmail_user or not gmail_app_password:
		return False

	recipients = _normalize_recipients(config.EMAIL_RECIPIENT)
	if not recipients:
		return False

	message = f"Subject: {subject}\n\n{body}"

	try:
		with smtplib.SMTP("smtp.gmail.com", 587) as server:
			if os.getenv("DEBUG_SMTP", "").lower() in ("1", "true", "yes"):
				server.set_debuglevel(1)
			server.starttls()
			server.login(gmail_user, gmail_app_password)
			server.sendmail(gmail_user, recipients, message)
	except Exception:
		return False

	return True


def send_bot_started_alert(account_login: int | str, account_balance: float, server: str) -> bool:
	"""Send a notification that the bot has started successfully."""
	subject = "US30 Bot STARTED"
	body = (
		"The US30 signal bot has started and is now running.\n\n"
		f"Account:  {account_login}\n"
		f"Server:   {server}\n"
		f"Balance:  {account_balance:.2f}\n"
	)
	return _smtp_send(subject, body)


def send_bot_stopped_alert(reason: str) -> bool:
	"""Send a plain email notification that the bot has stopped automatically."""
	subject = "US30 Bot STOPPED — automatic shutdown"
	body = (
		"The US30 signal bot has stopped automatically.\n\n"
		f"Reason: {reason}\n\n"
		"Please check the bot logs and restart manually if required."
	)
	return _smtp_send(subject, body)


def send_no_signal_alert(minutes_since_last: int) -> bool:
	"""Send an email when no buy/sell signal has fired within the configured interval."""
	subject = "US30 Bot — No Signal"
	body = (
		f"No buy or sell signal has been detected in the last {minutes_since_last} minute(s).\n\n"
		"The bot is still running and monitoring the market.\n"
		"This alert will repeat every time the silence window elapses with no new signal."
	)
	return _smtp_send(subject, body)
