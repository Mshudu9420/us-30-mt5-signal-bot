"""MT5 connection helpers for live terminal and Linux mock development."""

from __future__ import annotations

import time

import pandas as pd

import config

try:
	import MetaTrader5 as mt5
except ImportError:  # pragma: no cover - used in Linux dev environments.
	import mt5_mock as mt5


def connect() -> bool:
	"""Initialize MT5 with retry logic and print connected account details.

	Retries up to config.MAX_RETRIES times, waiting config.RETRY_DELAY_SECONDS
	between attempts. Returns False and exits gracefully on exhaustion.
	"""
	for attempt in range(1, config.MAX_RETRIES + 1):
		initialized = mt5.initialize()
		if initialized:
			account = mt5.account_info()
			if account is None:
				print("MT5 connected but account info is unavailable.")
				return False
			print("MT5 connected")
			print(f"login={account.login} server={account.server} balance={account.balance}")
			return True

		error = mt5.last_error() if hasattr(mt5, "last_error") else (None, "Unknown error")
		print(f"MT5 initialization failed (attempt {attempt}/{config.MAX_RETRIES}): {error}")
		if attempt < config.MAX_RETRIES:
			print(f"Retrying in {config.RETRY_DELAY_SECONDS}s...")
			time.sleep(config.RETRY_DELAY_SECONDS)

	print("MT5 connection failed: max retries reached. Exiting.")
	return False


def disconnect() -> None:
	"""Cleanly shut down the MT5 connection."""
	mt5.shutdown()
	print("MT5 disconnected")


def get_ohlcv(symbol: str, timeframe: int, n_bars: int) -> pd.DataFrame | None:
	"""Fetch n_bars of OHLCV data for symbol/timeframe.

	Returns a pandas DataFrame with columns:
	  time, open, high, low, close, tick_volume, spread, real_volume.
	Returns None if no data is returned by MT5.
	"""
	fallbacks = list(getattr(config, "SYMBOL_FALLBACKS", []))
	candidates: list[str] = []
	for candidate in [symbol, *fallbacks]:
		if candidate and candidate not in candidates:
			candidates.append(candidate)

	for candidate_symbol in candidates:
		rates = mt5.copy_rates_from_pos(candidate_symbol, timeframe, 0, n_bars)
		# mt5.copy_rates_from_pos may return None, an empty sequence, or array-like.
		# Avoid using `if not rates:` because pandas DataFrame truth-value is ambiguous
		# and raises ValueError. Check explicitly for None or empty length instead.
		if rates is None:
			continue
		if hasattr(rates, "__len__") and len(rates) == 0:
			continue

		if candidate_symbol != symbol:
			print(f"get_ohlcv: using fallback symbol {candidate_symbol} for requested {symbol}")

		# Build DataFrame and convert timestamps to configured timezone
		df = pd.DataFrame(rates)
		# Parse MT5 timestamps as UTC then convert to configured timezone (SAST by default)
		# config.TIMEZONE is read from config.py and should be a tz database name
		# supported by pandas (e.g. 'Africa/Johannesburg').
		df["time"] = pd.to_datetime(df["time"], unit="s", utc=True).dt.tz_convert(config.TIMEZONE)
		return df

	print(f"get_ohlcv: no data returned for {symbol} tf={timeframe}")
	return None


def place_market_order(
	symbol: str,
	direction: str,
	volume: float,
	sl: float | None = None,
	tp: float | None = None,
	deviation: int | None = None,
	magic: int | None = None,
) -> dict:
	"""Place a market order using the MetaTrader5 terminal.

	Returns a dict containing at least `success` (bool) and either `order` or
	`error` keys with additional details.

	Note: This function will attempt to use the real MetaTrader5 API when
	available. In test/mock environments it will return an explanatory
	failure message.
	"""
	# Provide defaults from config when not specified
	if deviation is None:
		deviation = getattr(config, "ORDER_DEVIATION", 20)
	if magic is None:
		magic = getattr(config, "ORDER_MAGIC", 0)

	# Ensure MT5 API is available
	if not hasattr(mt5, "order_send"):
		return {"success": False, "error": "MT5 order_send not available in this environment"}

	try:
		tick = mt5.symbol_info_tick(symbol)
		if tick is None:
			return {"success": False, "error": f"symbol tick info unavailable for {symbol}"}

		if direction == "BUY":
			price = float(tick.ask)
			order_type = mt5.ORDER_TYPE_BUY if hasattr(mt5, "ORDER_TYPE_BUY") else 0
		else:
			price = float(tick.bid)
			order_type = mt5.ORDER_TYPE_SELL if hasattr(mt5, "ORDER_TYPE_SELL") else 1

		request = {
			"action": mt5.TRADE_ACTION_DEAL,
			"symbol": symbol,
			"volume": float(volume),
			"type": order_type,
			"price": price,
			"sl": float(sl) if sl is not None else 0.0,
			"tp": float(tp) if tp is not None else 0.0,
			"deviation": int(deviation),
			"magic": int(magic),
			"comment": "us30-signal-bot",
			# default time/type if available
		}

		# Provide sensible defaults for filling/time if attributes exist
		if hasattr(mt5, "ORDER_TIME_GTC"):
			request["type_time"] = mt5.ORDER_TIME_GTC
		if hasattr(mt5, "ORDER_FILLING_FOK"):
			request["type_filling"] = mt5.ORDER_FILLING_FOK

		result = mt5.order_send(request)

		# Some MT5 wrappers return an object with retcode and order fields
		try:
			retcode = getattr(result, "retcode", None)
		except Exception:
			retcode = None

		return {"success": True, "result": result, "retcode": retcode}
	except Exception as exc:
		return {"success": False, "error": str(exc)}


def summarize_order_result(order_response: dict) -> dict:
	"""Return a concise, JSON-serializable summary for order responses.

	Accepts the dict returned by place_market_order and extracts the
	most useful fields for console/email reporting.
	"""
	summary: dict = {"success": bool(order_response.get("success", False))}
	if not summary["success"]:
		summary["error"] = order_response.get("error")
		return summary

	# Try to extract MT5 result details safely
	result = order_response.get("result")
	retcode = order_response.get("retcode")
	summary["retcode"] = retcode

	# Many MT5 wrappers return an object with 'order' or 'order_id' attributes
	order_id = None
	try:
		order_id = getattr(result, "order", None)
	except Exception:
		order_id = None
	if order_id is None:
		try:
			order_id = getattr(result, "order_id", None)
		except Exception:
			order_id = None
	if order_id is not None:
		summary["order_id"] = int(order_id)

	# Try to surface executed price/volume if available
	try:
		req = getattr(result, "request", None)
		if req and isinstance(req, dict):
			summary["volume"] = float(req.get("volume", 0))
			summary["price"] = float(req.get("price", 0))
	except Exception:
		pass

	return summary


def has_open_position(symbol: str, direction: str) -> bool:
	"""Return True if there is already an open position for symbol in the given direction.

	MT5 position type: 0 = BUY, 1 = SELL.
	Uses positions_get to fetch live positions; falls back to False if the call
	is unavailable (e.g. in mock environments that return an empty list).
	"""
	if not hasattr(mt5, "positions_get"):
		return False
	try:
		positions = mt5.positions_get(symbol=symbol)
	except Exception:
		return False
	if not positions:
		return False

	# Map direction string to MT5 position type integer
	target_type = 0 if direction == "BUY" else 1
	for pos in positions:
		pos_type = getattr(pos, "type", None)
		if pos_type is None and isinstance(pos, dict):
			pos_type = pos.get("type")
		if pos_type == target_type:
			return True
	return False
