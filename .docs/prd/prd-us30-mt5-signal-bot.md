# PRD: US30 MT5 Trading Signal Bot

**Feature Name:** us30-mt5-signal-bot  
**Version:** 1.0  
**Date:** 2025-04-12  
**Author:** Mashudu  

---

## 1. Introduction / Overview

This project is a Python-based trading signal bot that connects to a MetaTrader 5 (MT5) terminal via the `MetaTrader5` Python API. It monitors the US30 (Dow Jones CFD) instrument on an Exness MT5 account and generates **mean reversion trade signals** across three timeframes: M5, M15, and H1.

The bot does **not** place trades automatically. It outputs actionable signals to the console (and optionally via Telegram/email in future). It also calculates precise risk-based lot sizes and stop loss / take profit levels based on the trader's configured capital and risk percentage.

The goal is to give a small-capital trader ($100–$120) a structured, rule-based signal system for scalping US30 with disciplined risk management.

---

## 2. Goals

- G1: Generate mean reversion buy/sell signals for US30 using Bollinger Bands + RSI across M5, M15, and H1 timeframes.
- G2: Use H1 as a trend bias filter — only take M5/M15 signals aligned with H1 direction.
- G3: Calculate lot size, stop loss (in pips), and take profit for every signal based on a configurable risk % of initial capital.
- G4: Support manual toggle between 5% risk and 10% risk per trade via a config flag.
- G5: Run continuously on a Windows machine with MT5 terminal open, polling on a configurable interval.
- G6: Output signals clearly to the console with all relevant trade parameters.
- G7: Be easy to configure — symbol, capital, risk level, timeframes, and indicator settings all in one `config.py`.

---

## 3. User Stories

### US-01 — Signal Generation
> As a trader, I want to receive a clear buy or sell signal for US30 on M5/M15 when price is in an extreme mean-reversion zone, so that I know when a potential scalp opportunity exists.

**Acceptance Criteria:**
- Signal is generated when RSI is oversold (<30) or overbought (>70) AND price is outside the lower or upper Bollinger Band on M5 or M15.
- Signal includes direction (BUY/SELL), timeframe, entry price, and timestamp.

---

### US-02 — H1 Trend Filter
> As a trader, I want M5/M15 signals to be filtered by the H1 trend bias, so that I avoid trading against the dominant direction.

**Acceptance Criteria:**
- H1 bias is determined by price position relative to H1 20-period EMA (above = bullish, below = bearish).
- BUY signals are only shown if H1 bias is bullish.
- SELL signals are only shown if H1 bias is bearish.
- If no H1 bias is established, signals are suppressed with a console note.

---

### US-03 — Risk-Based Lot Sizing
> As a trader, I want the bot to calculate my lot size automatically based on my capital and risk percentage, so that I never risk more than my set amount per trade.

**Acceptance Criteria:**
- Bot reads `initial_capital` (e.g. $100) and `risk_percent` (5% or 10%) from config.
- Risk amount = `initial_capital × risk_percent`.
- Lot size is calculated as: `risk_amount / (stop_loss_pips × pip_value)`.
- Result is rounded to nearest 0.01 lot.
- If calculated lot is below broker minimum (0.01), bot warns the user in console output.

---

### US-04 — Stop Loss & Take Profit Output
> As a trader, I want each signal to include a stop loss and take profit level in price terms, so that I can manually enter the trade with proper parameters.

**Acceptance Criteria:**
- Stop loss is placed beyond the Bollinger Band that was breached (band value + buffer in pips).
- Take profit targets the Bollinger Band midline (20-period MA).
- Both values are shown as actual price levels (not just pips).

---

### US-05 — Risk Toggle
> As a trader, I want to manually switch between 5% and 10% risk per trade by changing a single config value, so that I can scale up when I feel confident.

**Acceptance Criteria:**
- `config.py` contains a `RISK_MODE` flag: `"conservative"` (5%) or `"aggressive"` (10%).
- Changing this flag and restarting the bot applies the new risk level immediately.
- Console output always states the active risk mode and dollar amount at startup.

---

### US-06 — Continuous Polling Loop
> As a trader, I want the bot to run in a loop and check for new signals at regular intervals, so that I don't have to manually trigger it.

**Acceptance Criteria:**
- Bot polls MT5 data every configurable number of seconds (default: 60s).
- Bot prints a heartbeat message each cycle showing time and current price.
- Bot handles MT5 disconnection gracefully with a retry mechanism and console warning.

---

### US-07 — Startup Configuration Summary
> As a trader, I want the bot to print a clear summary when it starts, so that I can confirm the settings before it begins scanning.

**Acceptance Criteria:**
- On startup, bot prints: symbol, broker, capital, risk mode, risk amount per trade, timeframes, and indicator settings.
- Bot confirms MT5 connection and account details (login, server, balance).

---

## 4. Functional Requirements

1. The system must connect to MT5 via the `MetaTrader5` Python library on startup.
2. The system must pull OHLCV data for US30 on M5, M15, and H1 timeframes.
3. The system must calculate a 20-period Bollinger Band (2 std dev) on each timeframe.
4. The system must calculate a 14-period RSI on M5 and M15.
5. The system must calculate a 20-period EMA on H1 for trend bias.
6. The system must generate a signal only when BB and RSI conditions are simultaneously met on M5 or M15.
7. The system must suppress signals that conflict with the H1 EMA bias.
8. The system must calculate lot size, SL price, and TP price for every valid signal.
9. The system must enforce a minimum lot of 0.01 and warn if the risk budget cannot support it.
10. The system must output signals to the console in a readable, structured format.
11. The system must read all configurable parameters from a single `config.py` file.
12. The system must run in a continuous loop with a user-defined polling interval.
13. The system must handle MT5 connection errors without crashing — log the error and retry.

---

## 5. Non-Goals (Out of Scope for v1.0)

- **No automated trade execution** — the bot does not place, modify, or close orders.
- **No backtesting engine** — historical performance analysis is out of scope.
- **No Telegram or email alerts** — console output only in v1.0.
- **No GUI or dashboard** — terminal/console interface only.
- **No machine learning** — rule-based logic only.
- **No multi-symbol support** — US30 only.
- **No news/economic calendar filter.**

---

## 6. Design Considerations

- All output should be clearly readable in a terminal window.
- Use colour-coded console output where possible (`colorama` library) — green for BUY, red for SELL.
- Signal output block should be visually distinct (bordered or dashed separator).
- Heartbeat / idle messages should be less visually prominent than signals.

---

## 7. Technical Considerations

- **Language:** Python 3.10+
- **MT5 Library:** `MetaTrader5` (pip installable, Windows only)
- **Indicator Library:** `pandas` + `pandas-ta` or manual calculation
- **Broker:** Exness — US30 symbol may be listed as `US30` or `US30.cash` — must be confirmed at runtime
- **Pip value for US30:** Approximately $1 per pip at 0.01 lot (to be confirmed per Exness specs)
- **Minimum lot size:** 0.01 on Exness US30
- **Platform requirement:** Windows (MT5 Python API is Windows-only)
- **Project structure:**

```
us30_bot/
├── config.py           # All user-configurable settings
├── mt5_connector.py    # MT5 connection and data fetching
├── indicators.py       # BB, RSI, EMA calculations
├── strategy.py         # Signal logic and H1 filter
├── risk_manager.py     # Lot size, SL, TP calculation
├── signal_output.py    # Console formatting and display
├── main.py             # Entry point and polling loop
└── tests/
    ├── test_indicators.py
    ├── test_strategy.py
    └── test_risk_manager.py
```

---

## 8. Success Metrics

- Bot connects to Exness MT5 and runs for 1 hour without crashing.
- At least one valid signal is generated and correctly displays lot size, SL, and TP.
- Risk amount per trade never exceeds the configured risk % of initial capital.
- H1 filter correctly suppresses at least one counter-trend signal during a test session.

---

## 9. Open Questions

- OQ-1: What is the exact US30 symbol name on Exness MT5? (e.g. `US30`, `US30Cash`, `DJIA`) — needs live verification.
- OQ-2: What is the exact pip/point value for US30 on Exness at 0.01 lot? Needed for accurate lot sizing.
- OQ-3: Does Exness allow 0.01 minimum lot on US30, or is it higher?
- OQ-4: Should the bot skip signals during non-US market hours (pre-9:30 AM ET), or trade 24h?
- OQ-5: Should the polling interval be different per timeframe (e.g. M5 checks every 5 min, H1 every hour)?
