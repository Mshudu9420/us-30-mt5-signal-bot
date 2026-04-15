"""Main entry point for the US30 MT5 signal bot."""

import config
import mt5_connector
from mt5_connector import connect
from signal_output import print_startup_summary


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


if __name__ == "__main__":
	main()
