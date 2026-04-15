"""Tests for risk_manager.py — Task 5.0"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from risk_manager import (
    calculate_lot_size,
    calculate_risk_amount,
    calculate_sl_price,
    calculate_tp_price,
)


# --- 5.1 calculate_risk_amount ---

def test_risk_amount_conservative():
    result = calculate_risk_amount(1000.0, "conservative")
    assert result == pytest.approx(50.0)


def test_risk_amount_aggressive():
    result = calculate_risk_amount(1000.0, "aggressive")
    assert result == pytest.approx(100.0)


def test_risk_amount_conservative_small_capital():
    result = calculate_risk_amount(100.0, "conservative")
    assert result == pytest.approx(5.0)


def test_risk_amount_invalid_mode_raises():
    with pytest.raises(ValueError):
        calculate_risk_amount(1000.0, "medium")


# --- 5.2 calculate_lot_size ---

def test_lot_size_normal():
    # risk=50, sl=10 pips, pip_value=1.0 → 50/10=5.0 lots
    result = calculate_lot_size(50.0, 10, 1.0)
    assert result == pytest.approx(5.0)


def test_lot_size_rounds_down():
    # risk=50, sl=7, pip_value=1.0 → 50/7=7.142... → floor to 7.14
    result = calculate_lot_size(50.0, 7, 1.0)
    assert result == pytest.approx(7.14)


def test_lot_size_enforces_minimum():
    # risk=0.001, sl=100, pip_value=1.0 → would be 0.00001 → clamped to MIN_LOT_SIZE 0.01
    result = calculate_lot_size(0.001, 100, 1.0)
    assert result == pytest.approx(0.01)


def test_lot_size_zero_pip_value_raises():
    with pytest.raises(ValueError):
        calculate_lot_size(50.0, 10, 0.0)


def test_lot_size_zero_sl_pips_raises():
    with pytest.raises(ValueError):
        calculate_lot_size(50.0, 0, 1.0)


# --- 5.3 calculate_sl_price ---

def test_sl_price_buy():
    # BUY: SL = band_value - buffer_pips (below lower band)
    result = calculate_sl_price("BUY", 39000.0, 10)
    assert result == pytest.approx(38990.0)


def test_sl_price_sell():
    # SELL: SL = band_value + buffer_pips (above upper band)
    result = calculate_sl_price("SELL", 39500.0, 10)
    assert result == pytest.approx(39510.0)


def test_sl_price_invalid_direction_raises():
    with pytest.raises(ValueError):
        calculate_sl_price("HOLD", 39000.0, 10)


# --- 5.4 calculate_tp_price ---

def test_tp_price_buy_returns_midline():
    result = calculate_tp_price("BUY", 39250.0)
    assert result == pytest.approx(39250.0)


def test_tp_price_sell_returns_midline():
    result = calculate_tp_price("SELL", 39250.0)
    assert result == pytest.approx(39250.0)


def test_tp_price_invalid_direction_raises():
    with pytest.raises(ValueError):
        calculate_tp_price("HOLD", 39250.0)
