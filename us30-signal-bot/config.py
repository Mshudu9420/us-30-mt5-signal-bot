"""Central configuration for the US30 MT5 signal bot."""

# Broker and symbol settings
BROKER_NAME = "Exness"
SYMBOL = "BTCUSDm"
SYMBOL_FALLBACKS = ["BTCUSD.cash", "BTCUSDCash", "BTCUSD"]

# Account and risk configuration
# INITIAL_CAPITAL is used as a fallback when the live MT5 account balance is
# unavailable (e.g. in tests or mock mode). In live operation the bot fetches
# the real account balance each cycle and uses that for lot-size calculations.
INITIAL_CAPITAL = 100.0
RISK_MODE = "conservative"  # Allowed: "conservative" (5%), "aggressive" (10%)
RISK_PERCENTS = {
	"conservative": 0.05,
	"aggressive": 0.10,
}
MIN_LOT_SIZE = 0.01
DEFAULT_PIP_VALUE = 1.0

# Timeframe configuration
TIMEFRAMES = {
	"entry": ["M1", "M5", "M15"],
	"bias": "H1",
}
N_BARS = 250

# Indicator settings
BB_PERIOD = 20
BB_STD_DEV = 2
RSI_PERIOD = 14
EMA_PERIOD = 50
# MACD settings (fast/slow EMA periods and signal line smoothing)
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL_PERIOD = 9

# Signal/risk parameters
SL_BUFFER_PIPS = 10
# Maximum allowed daily loss as a fraction of opening balance.
# Once this threshold is reached the bot stops placing orders for the rest of the day.
MAX_DAILY_LOSS_PCT = 0.05  # 5%
# Lot-size multiplier applied to medium-confidence (M5+M15) entries.
# Full-lot high-confidence entries always use 1.0.
MEDIUM_CONFIDENCE_LOT_MULTIPLIER = 0.5

# Runtime behavior
POLL_INTERVAL_SECONDS = 60
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 10
# Reconnect policy when the polling loop detects a dropped MT5 connection.
# Backoff doubles each attempt: attempt 1 = base, 2 = 2×base, 3 = 4×base, …
MT5_RECONNECT_ATTEMPTS = 5
MT5_RECONNECT_BACKOFF_BASE = 10  # seconds

# Alerts
ENABLE_EMAIL_ALERTS = True
EMAIL_RECIPIENT = "mmathidi01@gmail.com", "mementorelo@gmail.com"

# Timezone for timestamp display and logging. Default: South African Standard Time (SAST).
# Use a tz database name recognized by pandas (e.g. 'Africa/Johannesburg').
TIMEZONE = "Africa/Johannesburg"

# Logging
# Log files are written to the 'logs/' subdirectory next to this file.
# Each file is capped at 10 MB; up to 7 backups are kept (roughly one week of history).
LOG_DIR = "logs"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 7

# Trading session filter (New York time).
# Orders and alerts are suppressed outside this window.
TRADING_SESSION_TZ = "America/New_York"
TRADING_SESSION_START = (9, 30)   # 09:30 NY time
TRADING_SESSION_END = (16, 0)     # 16:00 NY time
# Symbols that trade 24/7 and are exempt from the NY session filter.
# Substrings are matched case-insensitively (e.g. "btc" matches "BTCUSDm").
SESSION_EXEMPT_SYMBOLS = ["btc", "eth", "xbt"]

# Automatic trading (disabled by default). Enable only after careful testing.
ENABLE_AUTO_TRADES = True
# Default order deviation (max allowed slippage in points)
ORDER_DEVIATION = 20
# Magic number for orders (optional)
ORDER_MAGIC = 20260423

# Additional live trading safety gate. Set to True only when you are ready
# to execute live trades against your real account. Kept separate so you can
# enable automated behavior in testing without opening live trading.
ENABLE_LIVE_TRADES = True
