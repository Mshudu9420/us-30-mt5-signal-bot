"""Main entry point for the US30 MT5 signal bot."""

import time

import config
import mt5_connector
from alerts import send_email_alert
from indicators import calculate_bollinger_bands, calculate_ema, calculate_macd, calculate_rsi, detect_fvg
from logger import get_logger
from mt5_connector import connect, disconnect, get_ohlcv
from risk_manager import (
	calculate_lot_size,
	calculate_risk_amount,
	calculate_rr_ratio,
	calculate_sl_price,
	calculate_tp_price,
	DailyLossTracker,
)
from signal_output import print_heartbeat, print_signal, print_startup_summary
from strategy import check_signal, get_h1_bias, get_macro_fvg_signal, is_high_confidence, is_in_trading_session, is_medium_confidence

_log = get_logger()


def main() -> bool:
	"""Initialize MT5 and print startup summary on launch."""
	if not connect():
		_log.error("Startup aborted: MT5 connection failed.")
		return False

	account_info = mt5_connector.mt5.account_info()
	if account_info is None:
		_log.error("Startup aborted: account info unavailable.")
		return False

	print_startup_summary(account_info, config)
	return True


def polling_loop() -> None:
	"""Fetch M5, M15, H1 data every poll cycle and calculate indicators."""
	try:
		from MetaTrader5 import TIMEFRAME_M1, TIMEFRAME_M5, TIMEFRAME_M15, TIMEFRAME_H1
	except ImportError:
		import mt5_mock as _mt5
		TIMEFRAME_M1 = _mt5.TIMEFRAME_M1
		TIMEFRAME_M5 = _mt5.TIMEFRAME_M5
		TIMEFRAME_M15 = _mt5.TIMEFRAME_M15
		TIMEFRAME_H1 = _mt5.TIMEFRAME_H1

	_daily_loss_tracker = DailyLossTracker(config.MAX_DAILY_LOSS_PCT)

	while True:
		# Use monotonic clock to keep a fixed-rate polling interval and report step timings.
		cycle_start = time.monotonic()
		try:
			step_times = {}
			# Fetch OHLCV (now includes 1-minute timeframe)
			fetch_start = time.monotonic()
			m1_df = get_ohlcv(config.SYMBOL, TIMEFRAME_M1, config.N_BARS)
			m5_df = get_ohlcv(config.SYMBOL, TIMEFRAME_M5, config.N_BARS)
			m15_df = get_ohlcv(config.SYMBOL, TIMEFRAME_M15, config.N_BARS)
			h1_df = get_ohlcv(config.SYMBOL, TIMEFRAME_H1, config.N_BARS)
			step_times["fetch"] = time.monotonic() - fetch_start

			# Indicators
			ind_start = time.monotonic()
			# Calculate indicators for 1-minute timeframe (Bollinger + RSI)
			if m1_df is not None:
				m1_df = calculate_bollinger_bands(m1_df, config.BB_PERIOD, config.BB_STD_DEV)
				m1_df = calculate_rsi(m1_df, config.RSI_PERIOD)
				m1_df = calculate_macd(m1_df, config.MACD_FAST, config.MACD_SLOW, config.MACD_SIGNAL_PERIOD)
				m1_fvgs = detect_fvg(m1_df)
			else:
				m1_fvgs = []

			if m5_df is not None:
				m5_df = calculate_bollinger_bands(m5_df, config.BB_PERIOD, config.BB_STD_DEV)
				m5_df = calculate_rsi(m5_df, config.RSI_PERIOD)
				m5_df = calculate_ema(m5_df, config.EMA_PERIOD)
				m5_df = calculate_macd(m5_df, config.MACD_FAST, config.MACD_SLOW, config.MACD_SIGNAL_PERIOD)

			if m15_df is not None:
				m15_df = calculate_bollinger_bands(m15_df, config.BB_PERIOD, config.BB_STD_DEV)
				m15_df = calculate_rsi(m15_df, config.RSI_PERIOD)
				m15_df = calculate_ema(m15_df, config.EMA_PERIOD)
				m15_df = calculate_macd(m15_df, config.MACD_FAST, config.MACD_SLOW, config.MACD_SIGNAL_PERIOD)

			if h1_df is not None:
				# Calculate Bollinger + RSI for H1 as well (used for multi-timeframe checks)
				h1_df = calculate_bollinger_bands(h1_df, config.BB_PERIOD, config.BB_STD_DEV)
				h1_df = calculate_rsi(h1_df, config.RSI_PERIOD)
				h1_df = calculate_ema(h1_df, config.EMA_PERIOD)
			step_times["indicators"] = time.monotonic() - ind_start

			# Signals and risk
			sig_start = time.monotonic()
			h1_bias = get_h1_bias(h1_df) if h1_df is not None else "UNCLEAR"

			m1_signal = check_signal(m1_df, "M1", h1_bias) if m1_df is not None else None
			m5_signal = check_signal(m5_df, "M5", h1_bias) if m5_df is not None else None
			m15_signal = check_signal(m15_df, "M15", h1_bias) if m15_df is not None else None

			# Use live account balance for risk calculations; fall back to config
			# INITIAL_CAPITAL if account info is unavailable (e.g. in tests/mock mode).
			_account_info = mt5_connector.mt5.account_info()
			_capital = float(_account_info.balance) if _account_info is not None else config.INITIAL_CAPITAL
			risk_amount = calculate_risk_amount(_capital, config.RISK_MODE)

			# Update daily loss tracker with the current balance so it can detect
			# a new trading day and record the opening balance automatically.
			_daily_loss_tracker.update(_capital)

			# Evaluate confidence tiers up-front so every signal print can show the label.
			_high_conf = is_high_confidence(m1_signal, m5_signal, m15_signal, h1_bias)
			_med_conf = (not _high_conf) and is_medium_confidence(m5_signal, m15_signal, h1_bias)

			for signal, df in ((m1_signal, m1_df), (m5_signal, m5_df), (m15_signal, m15_df)):
				if signal is None or df is None:
					continue
				direction = signal["direction"]
				entry = float(signal["entry_price"])
				latest_row = df.iloc[-1]
				sl_band = float(latest_row["bb_lower"] if direction == "BUY" else latest_row["bb_upper"])
				mid = float(latest_row["bb_mid"])
				sl = calculate_sl_price(direction, sl_band, config.SL_BUFFER_PIPS)
				tp = calculate_tp_price(direction, mid)
				lot = calculate_lot_size(risk_amount, abs(entry - sl), config.DEFAULT_PIP_VALUE)
				rr = calculate_rr_ratio(entry, sl, tp)
				risk_dict = {"lot_size": lot, "sl": sl, "tp": tp, "rr_ratio": rr}
				# Tag signal with confidence tier for display in print_signal
				tagged = dict(signal, is_high_confidence=_high_conf, is_medium_confidence=_med_conf)
				print_signal(tagged, risk_dict)
			step_times["signals"] = time.monotonic() - sig_start

			# Macro FVG analysis: use the latest M1 bar time as 'now' to stay
			# timezone-consistent with the fetched data.
			if m1_df is not None:
				_now = __import__("pandas").Timestamp(m1_df.iloc[-1]["time"])
				macro_sig = get_macro_fvg_signal(m1_df, m1_fvgs, _now)
				if macro_sig is not None:
					_log.info(
						f"macro-fvg | direction={macro_sig['direction']} "
						f"fvg=[{macro_sig['fvg_bottom']}-{macro_sig['fvg_top']}] "
						f"type={macro_sig['fvg_type']} "
						f"liquidity_target={macro_sig['liquidity_target']} "
						f"entry={macro_sig['entry_price']}"
					)

			# High-confidence handling: order + alert
			order_start = time.monotonic()
			if not is_in_trading_session(symbol=config.SYMBOL):
				_log.debug(
					f"session filter: outside NY trading hours "
					f"({config.TRADING_SESSION_START[0]:02d}:{config.TRADING_SESSION_START[1]:02d}–"
					f"{config.TRADING_SESSION_END[0]:02d}:{config.TRADING_SESSION_END[1]:02d} ET) — "
					f"no orders or alerts placed."
				)
			elif _high_conf:
				_sig = m1_signal or m5_signal or m15_signal
				_df = m5_df if m5_signal is not None else m15_df
				_direction = _sig["direction"]
				_entry = float(_sig["entry_price"])
				_row = _df.iloc[-1]
				_sl_band = float(_row["bb_lower"] if _direction == "BUY" else _row["bb_upper"])
				_sl = calculate_sl_price(_direction, _sl_band, config.SL_BUFFER_PIPS)
				_tp = calculate_tp_price(_direction, float(_row["bb_mid"]))
				_lot = calculate_lot_size(risk_amount, abs(_entry - _sl), config.DEFAULT_PIP_VALUE)
				_rr = calculate_rr_ratio(_entry, _sl, _tp)
				_alert_sig = dict(_sig, is_high_confidence=True)
				_risk_dict = {"lot_size": _lot, "sl": _sl, "tp": _tp, "rr_ratio": _rr}

				order_response = None
				order_summary = None
				if _daily_loss_tracker.is_triggered(_capital):
					_log.warning(
						f"circuit-breaker: daily loss limit reached "
						f"(opening={_daily_loss_tracker.opening_balance:.2f} "
						f"current={_capital:.2f} "
						f"limit={config.MAX_DAILY_LOSS_PCT * 100:.0f}%). "
						f"No orders will be placed today."
					)
					order_summary = {"success": False, "error": "DAILY_LOSS_LIMIT_HIT"}
				elif config.ENABLE_AUTO_TRADES:
					if config.ENABLE_LIVE_TRADES:
						if mt5_connector.has_open_position(config.SYMBOL, _direction):
							_log.info(f"auto-trade skipped: open {_direction} position already exists for {config.SYMBOL}")
							order_summary = {"success": False, "error": "DUPLICATE_POSITION"}
						else:
							order_response = mt5_connector.place_market_order(
								config.SYMBOL,
								_direction,
								_lot,
								_sl,
								_tp,
								deviation=getattr(config, "ORDER_DEVIATION", None),
								magic=getattr(config, "ORDER_MAGIC", None),
							)
							order_summary = mt5_connector.summarize_order_result(order_response)
							_log.info(f"auto-trade summary: {order_summary}")
					else:
						order_summary = {"success": False, "error": "LIVE_TRADES_DISABLED"}
						_log.info("auto-trade skipped: live trading disabled (ENABLE_LIVE_TRADES=False)")

				if order_summary is not None:
					_alert_sig["order_summary"] = order_summary
				if order_response is not None:
					_alert_sig["order_info"] = order_response

				# send alert (could block on SMTP)
				email_start = time.monotonic()
				send_email_alert(_alert_sig, _risk_dict)
				step_times["order_and_email"] = time.monotonic() - order_start
				step_times["email_send"] = time.monotonic() - email_start

			# Medium-confidence handling: alert only, half lot, no auto-trade.
			# Only fires when high-confidence did not already fire.
			elif _med_conf:
				_sig = m5_signal
				_df = m5_df
				_direction = _sig["direction"]
				_entry = float(_sig["entry_price"])
				_row = _df.iloc[-1]
				_sl_band = float(_row["bb_lower"] if _direction == "BUY" else _row["bb_upper"])
				_sl = calculate_sl_price(_direction, _sl_band, config.SL_BUFFER_PIPS)
				_tp = calculate_tp_price(_direction, float(_row["bb_mid"]))
				_lot = calculate_lot_size(risk_amount, abs(_entry - _sl), config.DEFAULT_PIP_VALUE)
				_lot = round(_lot * getattr(config, "MEDIUM_CONFIDENCE_LOT_MULTIPLIER", 0.5), 2)
				_rr = calculate_rr_ratio(_entry, _sl, _tp)
				_alert_sig = dict(_sig, is_medium_confidence=True)
				_risk_dict = {"lot_size": _lot, "sl": _sl, "tp": _tp, "rr_ratio": _rr}
				_log.info(f"medium-confidence signal: {_direction} lot={_lot:.2f} (alert only, no auto-trade)")
				if not step_times.get("order_and_email"):
					email_start = time.monotonic()
					send_email_alert(_alert_sig, _risk_dict)
					step_times["order_and_email"] = time.monotonic() - order_start
					step_times["email_send"] = time.monotonic() - email_start

			# Heartbeat (print latest close/time)
			if m5_df is not None:
				latest = m5_df.iloc[-1]
				print_heartbeat(str(latest["time"]), float(latest["close"]))

			# Total cycle time and sleep to keep a fixed-rate cadence
			cycle_elapsed = time.monotonic() - cycle_start
			_log.debug(
				f"timings (s): fetch={step_times.get('fetch',0):.3f} "
				f"indicators={step_times.get('indicators',0):.3f} "
				f"signals={step_times.get('signals',0):.3f} "
				f"order_and_email={step_times.get('order_and_email',0):.3f} "
				f"total={cycle_elapsed:.3f}"
			)

			sleep_for = max(0.0, config.POLL_INTERVAL_SECONDS - cycle_elapsed)
			if sleep_for > 0:
				time.sleep(sleep_for)
		except KeyboardInterrupt:
			_log.info("Bot stopped by user.")
			disconnect()
			break
		except Exception as exc:
			_log.exception("Unexpected error in polling loop: %s", exc)
			time.sleep(min(5, config.POLL_INTERVAL_SECONDS))


if __name__ == "__main__":
	if main():
		polling_loop()
