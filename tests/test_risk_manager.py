# -*- coding: utf-8 -*-
import pytest
from src.risk.risk_manager import RiskManager


class FakeAssets:
    def __init__(self, total_asset):
        self.total_asset = total_asset


class FakeTrader:
    def __init__(self, total_asset=100000):
        self._asset = total_asset

    def get_assets(self):
        return FakeAssets(self._asset)


def test_prevent_large_single_position():
    t = FakeTrader(100000)
    rm = RiskManager(t, max_position_per_symbol=100, max_position_pct=0.5)
    sig = {"code": "600000.SH", "volume": 200, "price": 1}
    ok, reason = rm.check_order(sig)
    assert not ok and reason == "exceeds_symbol_limit"


def test_exceeds_position_pct():
    t = FakeTrader(100000)
    rm = RiskManager(t, max_position_pct=0.01)  # only 1% allowed
    sig = {"code": "600000.SH", "volume": 200, "price": 1}  # value 200 -> 0.2% -> ok
    ok, _ = rm.check_order(sig)
    assert ok
    sig2 = {
        "code": "600001.SH",
        "volume": 2000,
        "price": 1,
    }  # value 2000 -> 2% -> blocked
    ok2, reason = rm.check_order(sig2)
    assert not ok2 and reason == "exceeds_position_pct"


def test_halt_when_drawdown_exceeded():
    t = FakeTrader(100000)
    rm = RiskManager(t, max_drawdown=0.1)
    # Simulate drop in equity
    t._asset = 85000  # 15% drop
    sig = {"code": "600000.SH", "volume": 1, "price": 1}
    ok, reason = rm.check_order(sig)
    assert not ok and reason == "max_drawdown_exceeded"


def test_apply_trade_effect_updates_positions():
    t = FakeTrader(100000)
    rm = RiskManager(t)
    rm.apply_trade_effect("600000.SH", 100)
    assert rm.positions["600000.SH"] == 100
