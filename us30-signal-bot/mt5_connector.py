"""MT5 connection helpers for live terminal and Linux mock development."""

try:
	import MetaTrader5 as mt5
except ImportError:  # pragma: no cover - used in Linux dev environments.
	import mt5_mock as mt5


def connect() -> bool:
	"""Initialize MT5 and print connected account details."""
	initialized = mt5.initialize()
	if not initialized:
		error = mt5.last_error() if hasattr(mt5, "last_error") else (None, "Unknown error")
		print(f"MT5 initialization failed: {error}")
		return False

	account = mt5.account_info()
	if account is None:
		print("MT5 connected but account info is unavailable.")
		return False

	print("MT5 connected")
	print(f"login={account.login} server={account.server} balance={account.balance}")
	return True
