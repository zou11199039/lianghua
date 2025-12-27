# -*- coding: utf-8 -*-
import time
from src.trading.receipt_listener import ReceiptListener


class FakeTraderForListener:
    def __init__(self):
        self.order_statuses = [("ORD-1", "filled", None)]
        self.order_manager = None

    def query_pending_order_receipts(self):
        # return once then empty
        sts = list(self.order_statuses)
        self.order_statuses = []
        return sts


def test_listener_forwards_receipts(monkeypatch):
    t = FakeTraderForListener()

    # stub order manager to capture calls
    class OM:
        def __init__(self):
            self.handled = []

        def handle_receipt(self, order_id, status, info=None):
            self.handled.append((order_id, status))

    om = OM()
    t.order_manager = om

    rl = ReceiptListener(trader=t, poll_interval=0.1)
    rl.start()
    time.sleep(0.25)
    rl.stop()

    assert ("ORD-1", "filled") in om.handled
