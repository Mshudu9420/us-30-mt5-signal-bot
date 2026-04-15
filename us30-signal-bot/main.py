"""Main entry point for the US30 MT5 signal bot."""

import time

import config
import mt5_connector
from indicators import calculate_bollinger_bands, calculate_ema, calculate_rsi
from mt5_connector import connect, get_ohlcv
from risk_manager import (
	calculate_lot_size,
	calculate_risk_amount,
	calculate_rr_ratio,
	calculate_sl_price,
	calculate_tp_price,
)
from signal_output import print_heartbeat, print_signal, print_startup_summary
from strategy import check_signal, get_h1_bias


def main() -> bool:
	"""Initialize MT5 and print startup summary on launch."""
	if not connect():
		print("Startup aborted: MT5 connection failed.")
		return False

	account_info = mt5_connector.mt5.account_info()
	if account_info is None:
		print("Startup aborted: account info unavailable.")
		return False

	print_startup_summary(account_info, config)
	return True


def polling_loop() -> None:
	"""Fetch M5, M15, H1 data every poll cycle and calculate indicators."""
	try:
		from MetaTrader5 import TIMEFRAME_M5, TIMEFRAME_M15, TIMEFRAME_H1
	except ImportError:
		import mt5_mock as _mt5
		TIMEFRAME_M5 = _mt5.TIMEFRAME_M5
		TIMEFRAME_M15 = _mt5.TIMEFRAME_M15
		TIMEFRAME_H1 = _mt5.TIMEFRAME_H1

	while True:
		m5_df = get_ohlcv(config.SYMBOL, TIMEFRAME_M5, config.N_BARS)
		m15_df = get_ohlcv(config.SYMBOL, TIMEFRAME_M15, config.N_BARS)
		h1_df = get_ohlcv(config.SYMBOL, TIMEFRAME_H1, config.N_BARS)

		if m5_df is not None:
			m5_df = calculate_bollinger_bands(m5_df, config.BB_PERIOD, config.BB_STD_DEV)
			m5_df = calculate_rsi(m5_df, config.RSI_PERIOD)
			m5_df = calculate_ema(m5_df, config.EMA_PERIOD)

		if m15_df is not None:
			m15_df = calculate_bollinger_bands(m15_df, config.BB_PERIOD, config.BB_STD_DEV)
			m15_df = calculate_rsi(m15_df, config.RSI_PERIOD)
			m15_df = calculate_ema(m15_df, config.EMA_PERIOD)

		if h1_df is not None:
			h1_df = calculate_ema(h1_df, config.EMA_PERIOD)

		h1_bias = get_h1_bias(h1_df) if h1_df is not None else "UNCLEAR"

		m5_signal = check_signal(m5_df, "M5", h1_bias) if m5_df is not None else None
		m15_signal = check_signal(m15_df, "M15", h1_bias) if m15_df is not None else None

		risk_amount = calculate_risk_amount(config.INITIAL_CAPITAL, config.RISK_MODE)

		for signal, df in ((m5_signal, m5_df), (m15_signal, m15_df)):
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
			print_signal(signal, risk_dict)

		if m5_df is not None:
			latest = m5_df.iloc[-1]
			print_heartbeat(str(latest["time"]), float(latest["close"]))

		time.sleep(config.POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
	main()
