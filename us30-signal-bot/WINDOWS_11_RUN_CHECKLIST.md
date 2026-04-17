# Windows 11 Run and Pre-Live Checklist

## Step-by-Step Run Checklist (Windows 11)

### 1) Install prerequisites
- [ ] Install Python 3.11 to 3.13 (64-bit).
- [ ] Confirm Python is available in terminal: `py --version`.
- [ ] Install MetaTrader 5 (64-bit).
- [ ] Launch MT5 and log in to your Exness account.

### 2) Open project in terminal
- [ ] Open PowerShell or Command Prompt.
- [ ] Navigate to the project folder:
  - `cd C:\path\to\us30\us30-signal-bot`

### 3) Create and activate virtual environment
- [ ] Create venv:
  - `py -m venv .venv`
- [ ] Activate venv:
  - `.venv\Scripts\activate`

### 4) Install dependencies
- [ ] Upgrade pip:
  - `python -m pip install --upgrade pip`
- [ ] Install project dependencies:
  - `pip install -r requirements.txt`
- [ ] Ensure MT5 package is installed:
  - `pip show MetaTrader5`
- [ ] If missing, install it:
  - `pip install MetaTrader5`

### 5) Configure runtime values
- [ ] Open `config.py` and verify:
  - [ ] `SYMBOL` matches your broker symbol.
  - [ ] `INITIAL_CAPITAL`, `RISK_MODE`, `SL_BUFFER_PIPS`, `POLL_INTERVAL_SECONDS` are correct.
  - [ ] `ENABLE_EMAIL_ALERTS` is set as intended.
  - [ ] `EMAIL_RECIPIENT` contains valid destination email(s).

### 6) Configure optional email secrets
- [ ] Open `.env` and set:
  - [ ] `GMAIL_USER=your_email@gmail.com`
  - [ ] `GMAIL_APP_PASSWORD=your_app_password`
- [ ] If email is disabled, skip this section.

### 7) Verify tests
- [ ] Run all tests:
  - `python -m pytest -v`
- [ ] Confirm all tests pass before live run.

### 8) Prepare MT5 market data
- [ ] Keep MT5 terminal open.
- [ ] Ensure target symbol is visible in Market Watch.
- [ ] Open the symbol chart at least once to load history.

### 9) Run the bot
- [ ] Start bot:
  - `python main.py`
- [ ] Confirm startup summary appears.
- [ ] Confirm heartbeat appears at poll interval.

### 10) Observe behavior
- [ ] Confirm at least heartbeat logs continue.
- [ ] Confirm signals print when conditions are met.
- [ ] Confirm high-confidence signals can trigger email alerts (if enabled).

### 11) Stop safely
- [ ] Press `Ctrl+C` to stop.
- [ ] Confirm graceful shutdown message:
  - `Bot stopped by user.`
- [ ] Confirm disconnect message from MT5 connector.

---

## Pre-Live Checklist (Safety and Readiness)

### A) Environment readiness
- [ ] Running on Windows 11 (not Linux) for live MT5 connectivity.
- [ ] MT5 app is open and logged in to the intended account.
- [ ] Correct account type selected (demo first, then live).
- [ ] System time and timezone are correct.
- [ ] Stable internet connection.

### B) Strategy and risk controls
- [ ] `RISK_MODE` reviewed and intentionally chosen.
- [ ] `INITIAL_CAPITAL` matches account plan assumptions.
- [ ] `SL_BUFFER_PIPS` and `DEFAULT_PIP_VALUE` reviewed.
- [ ] Polling interval is acceptable for your machine and broker limits.

### C) Symbol and data checks
- [ ] `SYMBOL` is valid on your MT5 broker.
- [ ] At least one symbol fallback is available if primary fails.
- [ ] Recent OHLCV data can be retrieved in MT5.

### D) Alerts and credentials
- [ ] Email alerts setting (`ENABLE_EMAIL_ALERTS`) matches your intent.
- [ ] `.env` exists and has valid Gmail credentials (if enabled).
- [ ] Email recipient list is valid and tested.

### E) Operational safeguards
- [ ] Start with demo account run.
- [ ] Monitor first session manually.
- [ ] Confirm clean shutdown with `Ctrl+C`.
- [ ] Save logs/output for first live session review.

### F) Go-live decision
- [ ] Full test suite passed immediately before run.
- [ ] No unresolved errors in terminal at startup.
- [ ] You are ready to supervise the first production session.
