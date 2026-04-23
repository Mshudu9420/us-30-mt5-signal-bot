"""Quick manual test for the alerts.send_email_alert() function.

Usage:
  - Ensure your `.env` contains working GMAIL_USER and GMAIL_APP_PASSWORD (or set env vars).
  - From the repo root run:
      python -m tests.test_send_email

This will attempt to send a real email to the addresses configured in `config.EMAIL_RECIPIENT`.
Be careful: it will send a real email if credentials and recipients are correct.
"""

from dotenv import load_dotenv
import os
import traceback

# Ensure repo package import works if running as module
from alerts import send_email_alert
import config


def main():
    load_dotenv()

    gmail_user = os.getenv("GMAIL_USER")
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")
    print("GMAIL_USER:", gmail_user)
    print("GMAIL_APP_PASSWORD present:", bool(gmail_app_password))
    print("EMAIL_RECIPIENT from config:", config.EMAIL_RECIPIENT)

    signal = {
        "is_high_confidence": True,
        "direction": "BUY",
        "timeframe": "M5",
        "timestamp": "test-email",
        "entry_price": 12345.67,
    }
    risk = {"lot_size": 0.01, "sl": 12340.0, "tp": 12360.0, "rr_ratio": 1.0}

    try:
        ok = send_email_alert(signal, risk)
        print("send_email_alert returned:", ok)
    except Exception:
        print("send_email_alert raised an exception:")
        traceback.print_exc()


if __name__ == "__main__":
    main()
