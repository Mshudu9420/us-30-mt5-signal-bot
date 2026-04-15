# Task List: US30 MT5 Signal Bot

**PRD Reference:** `prd-us30-mt5-signal-bot.md`  
**Date:** 2025-04-12  
**Target:** Junior–Intermediate Python Developer  

---

## Relevant Files

- `config.py` — All user-configurable settings (capital, risk, symbol, timeframes, indicator params)
- `main.py` — Entry point, startup summary, and continuous polling loop
- `mt5_connector.py` — MT5 connection, disconnection handling, and OHLCV data fetching
- `mt5_mock.py` — Stub module that mimics MetaTrader5 for Linux dev/testing
- `indicators.py` — Bollinger Bands, RSI, and EMA calculations using pandas
- `strategy.py` — Signal generation logic and H1 trend filter
- `risk_manager.py` — Lot size, stop loss, and take profit calculation
- `signal_output.py` — Console formatting with colorama (BUY=green, SELL=red)
- `alerts.py` — Gmail SMTP email alert for high-confidence signals
- `.env` — Gmail credentials (never commit to Git)
- `.gitignore` — Excludes .env, __pycache__, *.log, venv/
- `requirements.txt` — All pip dependencies
- `README.md` — Setup and usage instructions
- `tests/test_mt5_connector.py` — Unit tests for connect, disconnect, get_ohlcv using mt5_mock
- `tests/test_indicators.py` — Unit tests for BB, RSI, EMA functions
- `tests/test_strategy.py` — Unit tests for signal logic and H1 filter
- `tests/test_risk_manager.py` — Unit tests for lot sizing, SL, TP
- `tests/test_alerts.py` — Unit tests for email alert formatting and trigger logic

---

### Notes

- Unit tests live in `tests/` and mirror the module they test.
- Use `pytest` to run tests: `pytest tests/` from the project root.
- MT5-dependent code must be tested inside the Windows 11 VM. All other modules are testable on Ubuntu Linux.
- Never commit `.env` — store Gmail App Password there only.
- One sub-task at a time. Do NOT proceed to the next sub-task without user approval.
- Mark each sub-task `[x]` when complete. Mark parent `[x]` when all sub-tasks are done.

---

## Tasks

- [x] 1.0 Project Setup & Environment Configuration

  - [x] 1.1 Initialise the project folder `us30-signal-bot/` with the full directory structure (all files as empty stubs)
  - [x] 1.2 Create `requirements.txt` with all dependencies: `MetaTrader5`, `pandas`, `pandas-ta`, `colorama`, `python-dotenv`, `pytest`
  - [x] 1.3 Create `.gitignore` excluding `.env`, `__pycache__/`, `*.log`, `venv/`, `*.pyc`
  - [x] 1.4 Create `config.py` with all configurable values: symbol, capital, risk mode, timeframes, BB/RSI/EMA settings, polling interval, SL buffer pips, email toggle
  - [x] 1.5 Create `.env` template file (with placeholder values, not real credentials) and document how to populate it in `README.md`
  - [x] 1.6 Initialise Git repo, create GitHub repository, and push initial project skeleton

- [x] 2.0 MT5 Connection & Data Feed

  - [x] 2.1 Create `mt5_mock.py` — stub that mimics `MetaTrader5` module interface (initialize, shutdown, account_info, copy_rates_from_pos) returning dummy data, for use on Linux
  - [x] 2.2 Write `mt5_connector.py` — `connect()` function that initialises MT5, prints account info (login, server, balance), and returns connection status
  - [x] 2.3 Write `disconnect()` function in `mt5_connector.py` that cleanly shuts down the MT5 connection
  - [x] 2.4 Write `get_ohlcv(symbol, timeframe, n_bars)` function that fetches N bars of OHLCV data and returns a pandas DataFrame
  - [x] 2.5 Add retry logic to `connect()` — if connection fails, wait 10 seconds and retry up to `MAX_RETRIES` (from config), then exit gracefully
  - [x] 2.6 Write unit tests in `tests/test_mt5_connector.py` using `mt5_mock.py` to test connect, disconnect, and get_ohlcv without a live MT5 terminal

- [x] 3.0 Indicators Module (BB, RSI, EMA)

  - [x] 3.1 Write `calculate_bollinger_bands(df, period, std_dev)` in `indicators.py` — returns upper band, lower band, and midline as new DataFrame columns
  - [x] 3.2 Write `calculate_rsi(df, period)` in `indicators.py` — returns RSI as a new DataFrame column
  - [x] 3.3 Write `calculate_ema(df, period)` in `indicators.py` — returns EMA as a new DataFrame column
  - [x] 3.4 Write `get_latest_values(df)` helper — returns the most recent row's BB, RSI, EMA, and close price as a dict
  - [x] 3.5 Write unit tests in `tests/test_indicators.py` using synthetic OHLCV DataFrames — test BB, RSI, EMA output types, shapes, and known values

- [x] 4.0 Strategy & Signal Logic (with H1 Filter)

  - [x] 4.1 Write `get_h1_bias(h1_df)` in `strategy.py` — returns `"BULLISH"`, `"BEARISH"`, or `"UNCLEAR"` based on close vs H1 EMA
  - [x] 4.2 Write `check_signal(df, timeframe, h1_bias)` in `strategy.py` — evaluates BB + RSI conditions and returns a signal dict `{direction, timeframe, entry_price, timestamp}` or `None`
  - [x] 4.3 Add H1 filter inside `check_signal` — suppress BUY if bias is BEARISH, suppress SELL if bias is BULLISH, suppress all if UNCLEAR
  - [x] 4.4 Write `is_high_confidence(m5_signal, m15_signal)` — returns `True` if both M5 and M15 produce the same direction signal simultaneously (used to trigger email alert)
  - [x] 4.5 Write unit tests in `tests/test_strategy.py` — test all bias outcomes, signal suppression by H1 filter, and high-confidence detection logic

- [x] 5.0 Risk Manager (Lot Sizing, SL, TP)

  - [x] 5.1 Write `calculate_risk_amount(capital, risk_mode)` in `risk_manager.py` — returns dollar risk based on RISK_MODE ("conservative"=5%, "aggressive"=10%)
  - [x] 5.2 Write `calculate_lot_size(risk_amount, sl_pips, pip_value)` — returns lot size rounded down to nearest 0.01, with minimum lot enforcement
  - [x] 5.3 Write `calculate_sl_price(direction, band_value, buffer_pips)` — returns SL price level below lower band (BUY) or above upper band (SELL)
  - [x] 5.4 Write `calculate_tp_price(direction, midline)` — returns TP price at BB midline
  - [x] 5.5 Write `calculate_rr_ratio(entry, sl, tp)` — returns risk:reward ratio as a float rounded to 2 decimal places
  - [x] 5.6 Write unit tests in `tests/test_risk_manager.py` — test risk amount, lot sizing edge cases (too small budget), SL/TP prices, and RR ratio

- [x] 6.0 Signal Output & Email Alerts

  - [x] 6.1 Write `print_startup_summary(account_info, config)` in `signal_output.py` — prints all active settings block using colorama for formatting
  - [x] 6.2 Write `print_heartbeat(timestamp, current_price)` — prints a low-prominence one-liner each poll cycle
  - [x] 6.3 Write `print_signal(signal_dict, risk_dict)` — prints a visually distinct signal block (dashed border) with direction in colour, lot size, SL, TP, and RR ratio
  - [x] 6.4 Write `send_email_alert(signal_dict, risk_dict)` in `alerts.py` — sends Gmail SMTP email with signal details when `is_high_confidence` is True
  - [x] 6.5 Add `.env` loading via `python-dotenv` in `alerts.py` — reads `GMAIL_USER` and `GMAIL_APP_PASSWORD` at runtime
  - [x] 6.6 Write unit tests in `tests/test_alerts.py` — test email body formatting and that send is only triggered on high-confidence signals (mock smtplib)

- [ ] 7.0 Main Polling Loop & Entry Point

  - [ ] 7.1 Write `main.py` — initialise MT5 connection and print startup summary on launch
  - [ ] 7.2 Add the main polling loop — fetch M5, M15, H1 data every N seconds (from config), calculate all indicators
  - [ ] 7.3 Call strategy functions inside the loop — get H1 bias, check M5 signal, check M15 signal
  - [ ] 7.4 Call risk manager for any valid signal — calculate lot, SL, TP, RR and pass to signal output
  - [ ] 7.5 Call `is_high_confidence` — if True, trigger `send_email_alert`
  - [ ] 7.6 Handle `KeyboardInterrupt` (Ctrl+C) gracefully — print "Bot stopped by user" and call `disconnect()`
  - [ ] 7.7 End-to-end smoke test inside Windows 11 VM — run `main.py` against live Exness MT5, confirm startup summary prints, heartbeat runs, and at least one signal or suppression message appears
```
