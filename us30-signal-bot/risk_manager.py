"""Risk management — lot sizing, SL, TP, RR calculations."""
import math
from datetime import date as _date
import config


class DailyLossTracker:
    """Track intra-day drawdown and trigger a circuit breaker when the threshold is hit.

    The opening balance is recorded the first time `update` is called each calendar
    day (based on the local system date).  When the current balance has fallen by
    `max_loss_pct` or more relative to that opening balance the circuit breaker is
    considered triggered and no new orders should be placed.

    The tracker resets automatically at midnight — the next call to `update` on a
    new calendar date records a fresh opening balance.
    """

    def __init__(self, max_loss_pct: float) -> None:
        self._max_loss_pct = max_loss_pct
        self._opening_balance: float | None = None
        self._trading_date: _date | None = None

    def update(self, current_balance: float, today: _date | None = None) -> None:
        """Record opening balance for the day; resets automatically on a new calendar date."""
        if today is None:
            today = _date.today()
        if self._trading_date != today:
            self._opening_balance = current_balance
            self._trading_date = today

    def is_triggered(self, current_balance: float) -> bool:
        """Return True when today's loss has reached or exceeded the configured threshold."""
        if self._opening_balance is None or self._opening_balance == 0:
            return False
        loss = self._opening_balance - current_balance
        return loss >= self._opening_balance * self._max_loss_pct

    @property
    def opening_balance(self) -> float | None:
        """The recorded opening balance for the current trading day."""
        return self._opening_balance


def calculate_risk_amount(capital: float, risk_mode: str) -> float:
    """Return dollar risk based on risk_mode.

    Args:
        capital: Account capital in dollars.
        risk_mode: "conservative" (5%) or "aggressive" (10%).

    Returns:
        Dollar amount to risk on the trade.

    Raises:
        ValueError: If risk_mode is not a recognised mode.
    """
    if risk_mode not in config.RISK_PERCENTS:
        raise ValueError(
            f"Unknown risk_mode '{risk_mode}'. "
            f"Expected one of: {list(config.RISK_PERCENTS.keys())}"
        )
    return capital * config.RISK_PERCENTS[risk_mode]


def calculate_lot_size(risk_amount: float, sl_pips: float, pip_value: float) -> float:
    """Return lot size, floored to nearest 0.01, with minimum lot enforcement.

    Args:
        risk_amount: Dollar amount to risk on the trade.
        sl_pips: Stop-loss distance in pips.
        pip_value: Dollar value per pip per lot.

    Returns:
        Lot size (float, >= MIN_LOT_SIZE).

    Raises:
        ValueError: If sl_pips or pip_value is zero.
    """
    if sl_pips == 0:
        raise ValueError("sl_pips must not be zero.")
    if pip_value == 0:
        raise ValueError("pip_value must not be zero.")
    raw = risk_amount / (sl_pips * pip_value)
    # Floor to nearest 0.01
    lot = math.floor(raw * 100) / 100
    return max(lot, config.MIN_LOT_SIZE)


def calculate_sl_price(direction: str, band_value: float, buffer_pips: float) -> float:
    """Return stop-loss price level.

    BUY signals: SL is placed below the lower Bollinger Band.
    SELL signals: SL is placed above the upper Bollinger Band.

    Args:
        direction: "BUY" or "SELL".
        band_value: The relevant band price (lower for BUY, upper for SELL).
        buffer_pips: Additional pips buffer beyond the band.

    Returns:
        SL price as a float.

    Raises:
        ValueError: If direction is not "BUY" or "SELL".
    """
    if direction == "BUY":
        return band_value - buffer_pips
    elif direction == "SELL":
        return band_value + buffer_pips
    else:
        raise ValueError(f"Unknown direction '{direction}'. Expected 'BUY' or 'SELL'.")


def calculate_tp_price(direction: str, midline: float) -> float:
    """Return take-profit price level at the Bollinger Band midline.

    Args:
        direction: "BUY" or "SELL".
        midline: The Bollinger Band midline price.

    Returns:
        TP price as a float.

    Raises:
        ValueError: If direction is not "BUY" or "SELL".
    """
    if direction not in {"BUY", "SELL"}:
        raise ValueError(f"Unknown direction '{direction}'. Expected 'BUY' or 'SELL'.")
    return midline


def calculate_rr_ratio(entry: float, sl: float, tp: float) -> float:
    """Return the risk-reward ratio rounded to 2 decimal places.

    Args:
        entry: Entry price.
        sl: Stop-loss price.
        tp: Take-profit price.

    Returns:
        Risk-reward ratio as a float.

    Raises:
        ValueError: If the stop-loss distance from entry is zero.
    """
    risk_distance = abs(entry - sl)
    if risk_distance == 0:
        raise ValueError("entry and sl must not be equal.")
    reward_distance = abs(tp - entry)
    return round(reward_distance / risk_distance, 2)
