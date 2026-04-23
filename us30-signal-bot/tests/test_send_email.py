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

    order_response = None
    order_summary = None

    # Try to import mt5_connector and place a real order only if both auto-trade flags are enabled.
    try:
        import mt5_connector
    except Exception as e:
        mt5_connector = None
        print("mt5_connector import unavailable:", e)

    can_place = (
        mt5_connector is not None
        and getattr(config, "ENABLE_AUTO_TRADES", False)
        and getattr(config, "ENABLE_LIVE_TRADES", False)
        and getattr(mt5_connector, "place_market_order", None) is not None
    )

    if can_place:
        print("Attempting a real order placement via mt5_connector.place_market_order...")
        try:
            order_response = mt5_connector.place_market_order(
                getattr(config, "SYMBOL", "US30"),
                signal["direction"],
                float(risk["lot_size"]),
                float(risk["sl"]),
                float(risk["tp"]),
                deviation=getattr(config, "ORDER_DEVIATION", None),
                magic=getattr(config, "ORDER_MAGIC", None),
            )
            if getattr(mt5_connector, "summarize_order_result", None) is not None:
                order_summary = mt5_connector.summarize_order_result(order_response)
            else:
                order_summary = {"success": order_response.get("success", False)}
            print("Order response:", order_response)
            print("Order summary:", order_summary)
        except Exception as e:
            print("Placing real order raised an exception:", e)
            traceback.print_exc()
            order_response = {"success": False, "error": str(e)}
            order_summary = {"success": False, "error": str(e)}
    else:
        print("Not placing a real order; simulating an order response for email test.")
        # Simulate an order response similar to what place_market_order would return
        order_response = {
            "success": True,
            "retcode": 10009,
            "order": 123456,
            "ticket": 123456,
            "volume": float(risk["lot_size"]),
            "price": float(signal["entry_price"]),
            "comment": "SIMULATED_ORDER",
        }
        order_summary = {
            "success": True,
            "order_id": order_response["order"],
            "volume": order_response["volume"],
            "price": order_response["price"],
            "note": "SIMULATED",
        }

    # Attach order_info and order_summary to the signal so alerts include them
    signal["order_info"] = order_response
    signal["order_summary"] = order_summary

    try:
        ok = send_email_alert(signal, risk)
        print("send_email_alert returned:", ok)
    except Exception:
        print("send_email_alert raised an exception:")
        traceback.print_exc()


if __name__ == "__main__":
    main()
