"""Tests for risk_manager.py — Task 5.0"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from risk_manager import calculate_risk_amount


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
