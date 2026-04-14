# User Stories: US30 MT5 Signal Bot

**PRD Reference:** `prd-us30-mt5-signal-bot.md`  
**Date:** 2025-04-12  

---

## US-01 — Signal Generation

**As a** trader,  
**I want** to receive a clear buy or sell signal for US30 on M5/M15 when price is in a mean-reversion zone,  
**So that** I know when a scalp opportunity exists without watching the chart constantly.

### Acceptance Criteria
- [ ] Signal fires when RSI < 30 (oversold) AND price is below lower Bollinger Band → BUY signal
- [ ] Signal fires when RSI > 70 (overbought) AND price is above upper Bollinger Band → SELL signal
- [ ] Signal includes: direction, timeframe, entry price, timestamp
- [ ] Signals are checked on both M5 and M15 independently
- [ ] No signal fires when RSI and BB conditions are not both met simultaneously

---

## US-02 — H1 Trend Filter

**As a** trader,  
**I want** M5/M15 signals to only show when they align with the H1 trend direction,  
**So that** I avoid scalping against the dominant move.

### Acceptance Criteria
- [ ] H1 bias = BULLISH when close > 20-period EMA on H1
- [ ] H1 bias = BEARISH when close < 20-period EMA on H1
- [ ] BUY signals are shown only when H1 bias is BULLISH
- [ ] SELL signals are shown only when H1 bias is BEARISH
- [ ] If H1 bias is unclear (price at EMA), signals are suppressed with console note: "H1 bias unclear — no signals"

---

## US-03 — Risk-Based Lot Sizing

**As a** trader,  
**I want** the bot to calculate the correct lot size for each signal based on my capital and risk %,  
**So that** I never accidentally over-risk on a trade.

### Acceptance Criteria
- [ ] `initial_capital` and `risk_percent` are read from `config.py`
- [ ] Risk amount = `initial_capital × risk_percent / 100`
- [ ] Lot size formula: `risk_amount / (stop_loss_pips × pip_value_per_lot)`
- [ ] Result is rounded down to nearest 0.01
- [ ] If calculated lot < 0.01, bot prints: "⚠️ Risk budget too small for minimum lot — consider adjusting SL or increasing capital"
- [ ] Lot size is included in every signal output

---

## US-04 — Stop Loss & Take Profit Output

**As a** trader,  
**I want** each signal to show me the SL and TP price levels,  
**So that** I can enter the trade manually with exact parameters.

### Acceptance Criteria
- [ ] SL for BUY = lower Bollinger Band − buffer (configurable, default 10 pips)
- [ ] SL for SELL = upper Bollinger Band + buffer (configurable, default 10 pips)
- [ ] TP for BUY = Bollinger Band midline (20-period MA)
- [ ] TP for SELL = Bollinger Band midline (20-period MA)
- [ ] Both SL and TP are displayed as actual price values (not just pip distance)
- [ ] Risk:Reward ratio is calculated and displayed alongside the signal

---

## US-05 — Risk Toggle (Conservative / Aggressive)

**As a** trader,  
**I want** to switch between 5% and 10% risk by changing one config value,  
**So that** I can scale my risk up or down without editing the codebase.

### Acceptance Criteria
- [ ] `config.py` has a `RISK_MODE` setting: `"conservative"` or `"aggressive"`
- [ ] `"conservative"` maps to 5% risk per trade
- [ ] `"aggressive"` maps to 10% risk per trade
- [ ] On startup, bot prints active mode: e.g. `"Risk Mode: CONSERVATIVE — $5.00 per trade"`
- [ ] Restarting the bot with a changed `RISK_MODE` immediately applies the new %

---

## US-06 — Continuous Polling Loop

**As a** trader,  
**I want** the bot to check for signals automatically at regular intervals,  
**So that** I don't have to run it manually each time.

### Acceptance Criteria
- [ ] Bot polls MT5 every N seconds (configurable in `config.py`, default: 60)
- [ ] Each poll cycle prints a heartbeat: timestamp + current US30 bid price
- [ ] If MT5 disconnects, bot prints error, waits 10 seconds, and retries connection
- [ ] Bot does not crash on disconnection — it retries up to a configurable max retries limit
- [ ] Bot can be stopped cleanly with `Ctrl+C`

---

## US-07 — Startup Configuration Summary

**As a** trader,  
**I want** the bot to show me all its active settings when it starts,  
**So that** I can confirm everything is correct before it begins scanning.

### Acceptance Criteria
- [ ] On startup, bot prints a summary block containing:
  - Symbol (e.g. `US30`)
  - Broker / Server (from MT5 account info)
  - Account login and balance
  - Initial capital (from config)
  - Risk mode and dollar risk per trade
  - Active timeframes
  - Indicator settings (BB period/std dev, RSI period, EMA period)
  - Polling interval
- [ ] Summary is printed before the first poll cycle begins
- [ ] If MT5 connection fails at startup, bot prints a clear error and exits gracefully

---

## Story Map Summary

| Story | Feature Area         | Priority |
|-------|----------------------|----------|
| US-01 | Signal Generation    | P1       |
| US-02 | H1 Trend Filter      | P1       |
| US-03 | Lot Sizing           | P1       |
| US-04 | SL / TP Output       | P1       |
| US-05 | Risk Toggle          | P2       |
| US-06 | Polling Loop         | P1       |
| US-07 | Startup Summary      | P2       |
