"""Central configuration for the US30 MT5 signal bot."""

# Broker and symbol settings
BROKER_NAME = "Exness"
SYMBOL = "US30m"
SYMBOL_FALLBACKS = ["US30.cash", "US30Cash", "DJIA"]

# Account and risk configuration
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
	"entry": ["M5", "M15"],
	"bias": "H1",
}
N_BARS = 250

# Indicator settings
BB_PERIOD = 20
BB_STD_DEV = 2
RSI_PERIOD = 14
EMA_PERIOD = 20

# Signal/risk parameters
SL_BUFFER_PIPS = 10

# Runtime behavior
POLL_INTERVAL_SECONDS = 60
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 10

# Alerts
ENABLE_EMAIL_ALERTS = True
EMAIL_RECIPIENT = "mmathidi01@gmail.com", "mementorelo@gmail.com"
