# Test Scenarios: US30 MT5 Trading Signal Bot

**Source PRD:** `.docs/prd/prd-us30-mt5-signal-bot.md`  
**Version:** 1.0  
**Date:** 2026-04-14

---

## 1. Scope

This document defines test scenarios for v1.0 of the US30 MT5 Trading Signal Bot, focusing on:

- Signal generation logic (Bollinger Bands + RSI)
- H1 trend filtering
- Risk and lot size calculations
- SL/TP output
- Risk mode toggle behavior
- Continuous polling and resilience
- Startup configuration and connection summary

Out-of-scope items from PRD non-goals (auto execution, backtesting, alerts, GUI, ML, multi-symbol) are included as negative test checks.

---

## 2. Test Environment

- OS: Windows machine with MT5 terminal installed and logged in
- Broker: Exness demo/live account
- Symbol candidate(s): `US30`, `US30.cash` (verify runtime mapping)
- Python: 3.10+
- Dependencies: `MetaTrader5`, `pandas`, indicator library (`pandas-ta` or internal implementation)
- Default polling interval: 60 seconds

---

## 3. Test Data and Baseline Config

Use a baseline config unless the scenario specifies overrides:

- `initial_capital = 100`
- `RISK_MODE = "conservative"` (5%)
- Timeframes: M5, M15, H1
- Bollinger: period 20, std 2
- RSI: period 14
- H1 EMA: period 20
- `poll_interval_seconds = 60`
- `symbol = "US30"` (or runtime-resolved equivalent)

---

## 4. Functional Test Scenarios

| ID | Requirement Mapping | Scenario | Preconditions | Steps | Expected Result | Priority |
|---|---|---|---|---|---|---|
| TS-001 | US-01, FR-6 | Generate BUY signal on M5 oversold condition | MT5 connected, valid M5 candles loaded | 1) Provide/identify M5 candle where close is below lower BB and RSI < 30. 2) Run strategy evaluation. | BUY signal emitted with timeframe=M5, entry price, timestamp. | High |
| TS-002 | US-01, FR-6 | Generate SELL signal on M15 overbought condition | MT5 connected, valid M15 candles loaded | 1) Provide/identify M15 candle where close is above upper BB and RSI > 70. 2) Run strategy evaluation. | SELL signal emitted with timeframe=M15, entry price, timestamp. | High |
| TS-003 | US-01, FR-6 | No signal when only RSI condition is met | MT5 connected | 1) Use candle with RSI < 30 but close not beyond lower BB. 2) Evaluate strategy. | No trade signal produced. | High |
| TS-004 | US-01, FR-6 | No signal when only BB breach is met | MT5 connected | 1) Use candle below lower BB but RSI >= 30. 2) Evaluate strategy. | No trade signal produced. | High |
| TS-005 | US-02, FR-5, FR-7 | Allow BUY only with bullish H1 bias | H1 price above H1 EMA20 | 1) Create M5/M15 BUY setup. 2) Evaluate with bullish bias. | BUY signal allowed and printed. | High |
| TS-006 | US-02, FR-5, FR-7 | Suppress BUY when H1 bias is bearish | H1 price below H1 EMA20 | 1) Create M5/M15 BUY setup. 2) Evaluate with bearish bias. | BUY suppressed with console note indicating H1 conflict. | High |
| TS-007 | US-02, FR-5, FR-7 | Suppress SELL when H1 bias is bullish | H1 price above H1 EMA20 | 1) Create M5/M15 SELL setup. 2) Evaluate with bullish bias. | SELL suppressed with console note indicating H1 conflict. | High |
| TS-008 | US-02, FR-5, FR-7 | Suppress signals when H1 bias cannot be determined | H1 data insufficient or exactly ambiguous rule result | 1) Evaluate strategy with missing/invalid H1 bias state. | No signal printed; explicit message states no H1 bias established. | High |
| TS-009 | US-03, FR-8, FR-9 | Conservative risk lot-size calculation | `initial_capital=100`, `RISK_MODE=conservative`, known SL pips and pip value | 1) Start bot. 2) Trigger valid signal with SL pips=50 and pip value assumption. | Risk amount = $5; lot size = `risk / (SL*pip_value)` rounded to 0.01. | High |
| TS-010 | US-03, US-05, FR-8, FR-11 | Aggressive risk lot-size calculation after mode switch | Config editable, bot restart possible | 1) Set `RISK_MODE=aggressive`. 2) Restart bot. 3) Trigger same signal as TS-009. | Risk amount = $10 and larger lot than conservative mode using same SL/pip value. | High |
| TS-011 | US-03, FR-9 | Minimum lot warning when computed lot < 0.01 | Very wide SL or small capital to force tiny lot | 1) Trigger valid signal with high SL pips. | Console warns risk budget cannot support broker minimum lot (0.01). | High |
| TS-012 | US-04, FR-8 | Stop-loss price placement beyond breached Bollinger band + buffer | Signal candidate available | 1) Trigger BUY and SELL scenarios. 2) Inspect computed SL values. | SL price is beyond breached band by configured buffer in pips, side-correct. | High |
| TS-013 | US-04, FR-8 | Take-profit targets BB midline | Valid signal generated | 1) Trigger signal. 2) Compare TP to BB middle line. | TP equals or matches expected middle-band target in price terms. | High |
| TS-014 | US-04, FR-10 | Signal output contains all required fields | Valid signal generated | 1) Capture console output for signal block. | Includes direction, timeframe, entry, SL, TP, lot size, timestamp. | High |
| TS-015 | US-05, FR-11 | Risk mode reflected in startup summary | Bot starts with config set | 1) Start in conservative mode. 2) Restart in aggressive mode. | Startup summary shows active mode and corresponding dollar risk in each run. | Medium |
| TS-016 | US-06, FR-12 | Polling loop runs at configured interval | MT5 connected | 1) Set poll interval to 60s. 2) Observe multiple cycles timestamps. | Loop executes approximately every configured seconds. | High |
| TS-017 | US-06, FR-12 | Heartbeat message printed every cycle | Polling loop active | 1) Observe console over at least 3 cycles with no signal event. | Heartbeat line printed each cycle with time and current price. | Medium |
| TS-018 | US-06, FR-13 | Graceful recovery on MT5 disconnection | Simulated or real temporary MT5 disconnect | 1) Disconnect MT5 or interrupt terminal access. 2) Keep bot running. 3) Restore connection. | Bot logs warning, retries without crash, reconnects and resumes polling. | High |
| TS-019 | US-07, FR-1, FR-11 | Startup summary and account confirmation | Valid account login | 1) Start bot. | Summary prints symbol, broker/server, capital, risk mode, risk amount, timeframes, indicator settings, account login/balance, connection status. | High |
| TS-020 | FR-2, FR-3, FR-4, FR-5 | Indicator computations present and consistent | Data fetch working | 1) Pull OHLCV for M5/M15/H1. 2) Inspect computed columns. | BB20/2σ on all TFs, RSI14 on M5/M15, EMA20 on H1 are available with expected non-null values after warmup. | High |
| TS-021 | FR-2 | Symbol runtime validation for Exness naming | Account with potential alternate symbol names | 1) Configure `US30`. 2) If unavailable, test fallback/mapping strategy. | Bot identifies valid tradable US30 symbol or exits with clear actionable error. | Medium |
| TS-022 | FR-10, Design | Console readability and color coding | Terminal supports colors | 1) Trigger BUY and SELL outputs. | BUY highlighted green, SELL red, heartbeat visually less prominent, output block structured. | Low |

---

## 5. Non-Goal Verification Scenarios

| ID | Non-Goal Mapping | Scenario | Steps | Expected Result |
|---|---|---|---|---|
| NG-001 | No auto execution | Ensure no orders are sent by bot | 1) Run bot during valid signal. 2) Inspect MT5 trade history/order tab. | Signal is informational only; no order send API call effect. |
| NG-002 | No backtesting engine | Confirm no backtest mode in v1.0 | 1) Review CLI/config options. | No historical simulation mode exposed. |
| NG-003 | No Telegram/email alerts | Confirm no external alert dispatch | 1) Trigger signal. 2) Inspect logs/network behavior. | Output appears in console only. |
| NG-004 | No GUI/dashboard | Confirm terminal-only interface | 1) Start bot. | No GUI application/web dashboard launched. |
| NG-005 | No multi-symbol support | Confirm US30-only processing | 1) Attempt config with second symbol list. | Bot supports only a single US30 symbol in v1.0. |

---

## 6. Edge and Error Scenarios

| ID | Area | Scenario | Expected Result | Priority |
|---|---|---|---|---|
| EE-001 | Data integrity | Insufficient candle history for indicators warmup | Bot skips evaluation with clear warning, no crash. | High |
| EE-002 | Data integrity | NaN values in fetched OHLCV | Bot validates and skips invalid cycle safely. | High |
| EE-003 | Config | Invalid `RISK_MODE` value | Startup fails fast with clear valid options (`conservative/aggressive`). | High |
| EE-004 | Config | Negative/zero `initial_capital` | Validation error with actionable message; processing halted. | High |
| EE-005 | Config | Invalid polling interval (0 or negative) | Validation error and safe default or halt per implementation choice. | Medium |
| EE-006 | Runtime | MT5 initialize/login failure at startup | Clear error + retry or safe exit; no stack trace crash loop. | High |
| EE-007 | Output | Extremely frequent signals in volatile market | Output remains structured and readable; no malformed lines. | Medium |

---

## 7. Traceability Matrix

| PRD Item | Covered By |
|---|---|
| US-01 | TS-001, TS-002, TS-003, TS-004 |
| US-02 | TS-005, TS-006, TS-007, TS-008 |
| US-03 | TS-009, TS-010, TS-011 |
| US-04 | TS-012, TS-013, TS-014 |
| US-05 | TS-010, TS-015 |
| US-06 | TS-016, TS-017, TS-018 |
| US-07 | TS-019 |
| FR-1..FR-13 | TS-001..TS-022, EE-001..EE-007 |
| Non-goals | NG-001..NG-005 |

---

## 8. Exit Criteria

Testing is considered complete for v1.0 when:

- All High-priority scenarios pass.
- No unresolved High-severity defects remain in signal logic, risk calculations, or loop stability.
- MT5 disconnect recovery is verified in at least one controlled failure test.
- Startup summary and signal payload fields are confirmed accurate against config and live data.
