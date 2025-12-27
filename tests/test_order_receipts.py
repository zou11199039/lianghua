# -*- coding: utf-8 -*-
from src.trading.order_manager import OrderManager


class FakeTraderWithReceipt:
    def __init__(self):
        self.handlers = []

    def register_receipt_handler(self, fn):
        self.handlers.append(fn)

    def execute_signal(self, signal):
        return "ORD-1"

    def simulate_receipt(self, order_id, status):
        for h in self.handlers:
            h(order_id, status, None)


def test_receipt_filled_applies_position():
    t = FakeTraderWithReceipt()
    om = OrderManager(t, paper_mode=False, max_retries=1)

    # attach simple risk manager
    class FakeRM:
        def __init__(self):
            self.applied = False

        def apply_trade_effect(self, code, qty):
            self.applied = True

    rm = FakeRM()
    om.risk_manager = rm

    oid = om.submit_signal(
        {"code": "600000.SH", "signal_type": "BUY", "volume": 100, "price": 10}
    )
    assert oid == "ORD-1"
    # simulate fill
    t.simulate_receipt("ORD-1", "filled")
    assert rm.applied is True


def test_receipt_failed_triggers_retry_then_fail():
    t = FakeTraderWithReceipt()
    # trader execute_signal returns same id; for simplicity we check status transitions
    om = OrderManager(t, paper_mode=False, max_retries=0)
    called = om.submit_signal(
        {"code": "600000.SH", "signal_type": "BUY", "volume": 100, "price": 10}
    )
    assert called == "ORD-1"
    # simulate failure -> since max_retries=0, should mark failed
    t.simulate_receipt("ORD-1", "failed")
    assert om.pending_orders["ORD-1"]["status"] == "failed"
