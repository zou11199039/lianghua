# -*- coding: utf-8 -*-
"""ReceiptListener: polls trader for order receipts and forwards them to OrderManager."""
import threading
import time
import logging
from typing import Callable

logger = logging.getLogger('quant_app.receipt_listener')

class ReceiptListener:
    def __init__(self, trader, poll_interval: float = 1.0, fetch_func: Callable = None):
        """Create a ReceiptListener.

        - trader: the trade executor or underlying trader which may provide query methods
        - poll_interval: seconds between polls
        - fetch_func: optional callable to fetch pending receipts; signature -> List[(order_id, status, info)]
        """
        self.trader = trader
        self.poll_interval = float(poll_interval)
        self._running = False
        self._thread = None
        # fetch_func(order_id_list) -> yields tuples (order_id, status, info)
        self.fetch_func = fetch_func

    def _default_fetch(self):
        """Default fetch strategy: if trader exposes "query_pending_order_receipts", call it."""
        try:
            if hasattr(self.trader, 'query_pending_order_receipts'):
                return self.trader.query_pending_order_receipts()
            # If trader has simulate_receipt generator for tests, do nothing here
        except Exception as e:
            logger.exception("Error fetching receipts: %s", e)
        return []

    def _run_loop(self):
        while self._running:
            try:
                receipts = []
                if callable(self.fetch_func):
                    receipts = self.fetch_func()
                else:
                    receipts = self._default_fetch()

                from src.trading.receipt_parser import parse_receipt
                for raw in receipts:
                    try:
                        # receipts may be in various shapes; normalize
                        parsed = None
                        # If fetch returns tuples (order_id, status, info) use directly
                        if isinstance(raw, tuple) and len(raw) >= 2:
                            parsed = (str(raw[0]), str(raw[1]), raw[2] if len(raw) >= 3 else None)
                        else:
                            # try parser
                            parsed = parse_receipt(raw)

                        if not parsed:
                            logger.warning(f"Could not parse receipt: {raw}")
                            continue

                        order_id, status, info = parsed

                        # forward to order manager if present
                        om = getattr(self.trader, 'order_manager', None) or getattr(self.trader, 'orderMgr', None)
                        if om and hasattr(om, 'handle_receipt'):
                            om.handle_receipt(order_id, status, info)
                        else:
                            # if trader itself handles receipts via callback, emit through trader
                            try:
                                if hasattr(self.trader, '_emit_receipt'):
                                    self.trader._emit_receipt(order_id, status, info)
                            except Exception:
                                pass
                    except Exception:
                        logger.exception("Error handling receipt %s", raw)
            except Exception:
                logger.exception("Receipt listener encountered an error")

            time.sleep(self.poll_interval)

    def start(self):
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            logger.info("Receipt listener started")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            logger.info("Receipt listener stopped")
