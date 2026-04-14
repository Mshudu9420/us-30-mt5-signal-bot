# US30 MT5 Signal Bot

Python-based MT5 signal bot for US30 mean reversion signals (M5/M15) with H1 trend filtering and risk-based sizing.

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure runtime values in `config.py`.
4. Populate `.env` for email alerts (optional):

```env
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=your_gmail_app_password
ALERT_RECIPIENT=recipient_email@gmail.com
```

## Notes

- Do not commit real credentials.
- `.env` is excluded by `.gitignore`.
- MT5 live connectivity must be tested on Windows with MT5 terminal running.
