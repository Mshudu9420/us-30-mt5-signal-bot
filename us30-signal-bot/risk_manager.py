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
