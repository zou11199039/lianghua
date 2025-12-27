# -*- coding: utf-8 -*-
import pytest
from src.trading.order_manager import OrderManager


class FakeTrader:
    def __init__(self, behavior='success'):
        self.behavior = behavior
        self.calls = 0

    def execute_signal(self, signal):
        self.calls += 1
        if self.behavior == 'success':
            return f"ORD-{self.calls}"
        if self.behavior == 'risk':
            return 'RISK_HALT'
        if self.behavior == 'fail_once':
            if self.calls == 1:
                raise Exception('Transient error')
            return f"ORD-{self.calls}"
        raise Exception('Hard failure')


def test_paper_mode_simulates_order():
    t = FakeTrader('success')
    om = OrderManager(t, paper_mode=True)
    oid = om.submit_signal({'code':'600000.SH','signal_type':'BUY'})
    assert oid and oid.startswith('PAPER-')


def test_successful_order_submission():
    t = FakeTrader('success')
    om = OrderManager(t, paper_mode=False)
    oid = om.submit_signal({'code':'600000.SH','signal_type':'BUY'})
    assert oid == 'ORD-1'


def test_risk_halt_propagates():
    t = FakeTrader('risk')
    om = OrderManager(t, paper_mode=False)
    oid = om.submit_signal({'code':'600000.SH','signal_type':'BUY'})
    assert oid == 'RISK_HALT'


def test_retry_on_transient_error():
    t = FakeTrader('fail_once')
    om = OrderManager(t, max_retries=2, retry_delay=0)
    oid = om.submit_signal({'code':'600000.SH','signal_type':'BUY'})
    assert oid == 'ORD-2'
