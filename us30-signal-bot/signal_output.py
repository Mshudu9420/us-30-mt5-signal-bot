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
