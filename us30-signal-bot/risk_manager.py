"""Risk management — lot sizing, SL, TP, RR calculations."""
import math
import config


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
