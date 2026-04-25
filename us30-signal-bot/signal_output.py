"""Console output helpers for bot status and trading signals."""

from colorama import Fore, Style, init


def print_startup_summary(account_info, config) -> None:
	"""Print a formatted startup summary of active bot settings."""
	init(autoreset=True, strip=False)

	border = f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}"
	title = f"{Fore.YELLOW}{Style.BRIGHT}US30 MT5 SIGNAL BOT{Style.RESET_ALL}"

	def line(label: str, value: str) -> str:
		return f"{Fore.GREEN}{label:<18}{Style.RESET_ALL} {value}"

	entry_timeframes = ", ".join(config.TIMEFRAMES["entry"])
	email_status = "ON" if config.ENABLE_EMAIL_ALERTS else "OFF"

	print(border)
	print(title)
	print(border)
	print(line("BROKER", config.BROKER_NAME))
	print(line("SYMBOL", config.SYMBOL))
	print(line("RISK MODE", config.RISK_MODE))
	print(line("ENTRY TIMEFRAMES", entry_timeframes))
	print(line("BIAS TIMEFRAME", config.TIMEFRAMES["bias"]))
	print(line("BB PERIOD", str(config.BB_PERIOD)))
	print(line("BB STD DEV", str(config.BB_STD_DEV)))
	print(line("RSI PERIOD", str(config.RSI_PERIOD)))
	print(line("EMA PERIOD", str(config.EMA_PERIOD)))
	print(line("SL BUFFER", str(config.SL_BUFFER_PIPS)))
	print(line("POLL INTERVAL", f"{config.POLL_INTERVAL_SECONDS}s"))
	print(line("EMAIL ALERTS", email_status))
	print(line("ACCOUNT LOGIN", str(account_info.login)))
	print(line("ACCOUNT SERVER", str(account_info.server)))
	print(line("ACCOUNT BALANCE", f"{account_info.balance:.2f}"))
	print(border)


def print_heartbeat(timestamp, current_price: float) -> None:
	"""Print a low-prominence one-line heartbeat for each poll cycle."""
	init(autoreset=True, strip=False)
	message = (
		f"{Style.DIM}{Fore.WHITE}heartbeat | {timestamp} | "
		f"price={current_price:.2f}{Style.RESET_ALL}"
	)
	print(message)


def print_signal(signal_dict, risk_dict) -> None:
	"""Print a visually distinct signal block with risk details."""
	init(autoreset=True, strip=False)

	direction = str(signal_dict.get("direction", "UNKNOWN")).upper()
	if direction == "BUY":
		direction_text = f"{Fore.GREEN}{Style.BRIGHT}{direction}{Style.RESET_ALL}"
	elif direction == "SELL":
		direction_text = f"{Fore.RED}{Style.BRIGHT}{direction}{Style.RESET_ALL}"
	else:
		direction_text = f"{Fore.YELLOW}{Style.BRIGHT}{direction}{Style.RESET_ALL}"

	# Confidence tier label and colour
	if signal_dict.get("is_high_confidence"):
		confidence_text = f"{Fore.GREEN}{Style.BRIGHT}HIGH CONFIDENCE{Style.RESET_ALL}"
	elif signal_dict.get("is_medium_confidence"):
		confidence_text = f"{Fore.YELLOW}{Style.BRIGHT}MEDIUM CONFIDENCE{Style.RESET_ALL}"
	else:
		confidence_text = f"{Style.DIM}UNCONFIRMED{Style.RESET_ALL}"

	border = f"{Fore.CYAN}{'-' * 60}{Style.RESET_ALL}"

	print(border)
	print(f"{Fore.MAGENTA}{Style.BRIGHT}SIGNAL{Style.RESET_ALL} {direction_text}")
	print(f"{Fore.GREEN}CONFIDENCE{Style.RESET_ALL}    {confidence_text}")
	print(f"{Fore.GREEN}TIMEFRAME{Style.RESET_ALL}      {signal_dict.get('timeframe', '-')}")
	print(f"{Fore.GREEN}TIMESTAMP{Style.RESET_ALL}      {signal_dict.get('timestamp', '-')}")
	print(f"{Fore.GREEN}ENTRY{Style.RESET_ALL}          {float(signal_dict.get('entry_price', 0.0)):.2f}")
	print(f"{Fore.GREEN}LOT SIZE{Style.RESET_ALL}       {float(risk_dict.get('lot_size', 0.0)):.2f}")
	print(f"{Fore.GREEN}SL{Style.RESET_ALL}             {float(risk_dict.get('sl', 0.0)):.2f}")
	print(f"{Fore.GREEN}TP{Style.RESET_ALL}             {float(risk_dict.get('tp', 0.0)):.2f}")
	print(f"{Fore.GREEN}RR{Style.RESET_ALL}             {float(risk_dict.get('rr_ratio', 0.0)):.2f}")
	print(border)
