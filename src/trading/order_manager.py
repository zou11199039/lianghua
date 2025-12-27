# -*- coding: utf-8 -*-
"""OrderManager handles signal submission and retries.

Also supports paper-mode simulation and simple compensation logic.
"""
import time
import uuid
import logging
from typing import Optional

logger = logging.getLogger("quant_app.order")


class OrderManager:
    def __init__(self, trader, max_retries=3, retry_delay=2, paper_mode=False):
        """Initialize OrderManager.

        trader: an object exposing execute_signal(signal) -> order_id or 'RISK_HALT'
        """
        self.trader = trader
        self.max_retries = int(max_retries)
        self.retry_delay = int(retry_delay)
        self.paper_mode = paper_mode

        # pending orders tracking: order_id -> {'signal':..., 'attempts': n}
        self.pending_orders = {}

        # if trader supports receipt callbacks, register
        try:
            self.trader.register_receipt_handler(self.handle_receipt)
        except Exception:
            pass

    def _simulate_order(self, signal: dict) -> str:
        # Return a synthetic order id for paper trading
        oid = f"PAPER-{int(time.time())}-{uuid.uuid4().hex[:6]}"
        logger.info(f"Paper order simulated: {oid} for {signal.get('code')}")
        return oid

    def submit_signal(self, signal: dict) -> Optional[str]:
        """Submit a signal and handle risk checks, retries and halts.

        Returns an order_id or None on failure.
        """
        # Risk check (if attached)
        rm = getattr(self, "risk_manager", None)
        if rm:
            ok, reason = rm.check_order(signal)
            if not ok:
                logger.warning(f"Order blocked by risk manager: {reason}")
                return "RISK_HALT"

        if self.paper_mode:
            oid = self._simulate_order(signal)
            # simulate applying trade effect
            if getattr(self, "risk_manager", None) and oid:
                self.risk_manager.apply_trade_effect(
                    signal.get("code"), int(signal.get("volume", 0))
                )
            # mark pending as simulated filled
            self.pending_orders[oid] = {
                "signal": signal,
                "attempts": 0,
                "status": "filled",
            }
            return oid

        attempt = 0
        last_exc = None
        while attempt <= self.max_retries:
            try:
                oid = self.trader.execute_signal(signal)
                # xt trader returns 'RISK_HALT' or some id
                if oid == "RISK_HALT" or not oid:
                    logger.warning(
                        f"Order rejected or empty id on attempt {attempt}: "
                        f"{oid}"
                    )
                    return "RISK_HALT"
                logger.info(f"Order placed: {oid} (attempt {attempt})")
                # record pending order and attempts
                self.pending_orders[oid] = {
                    "signal": signal,
                    "attempts": attempt,
                    "status": "submitted",
                }
                return oid
            except Exception as e:
                last_exc = e
                logger.exception(
                    f"Order submission failed on attempt {attempt}: {e}"
                )
                attempt += 1
                if attempt > self.max_retries:
                    break
                time.sleep(self.retry_delay)

        logger.error(f"Order failed after {self.max_retries} retries: {last_exc}")
        return None

    def handle_receipt(self, order_id: str, status: str, info=None):
        """Handle async receipt events from the broker/trader.

        status: 'filled'|'rejected'|'partial'|'canceled'|'failed'
        """
        rec = self.pending_orders.get(order_id)
        if not rec:
            logger.warning(f"Received receipt for unknown order {order_id}: {status}")
            return False

        if status == "filled" or status == "partial":
            # apply effect and finalize
            sig = rec["signal"]
            if getattr(self, "risk_manager", None):
                self.risk_manager.apply_trade_effect(
                    sig.get("code"), int(sig.get("volume", 0))
                )
            rec["status"] = "filled"
            logger.info(f"Order filled: {order_id}")
            return True

        if status in ("rejected", "failed"):
            # retry or mark failed
            rec["attempts"] += 1
            if rec["attempts"] <= self.max_retries:
                logger.info(
                    f"Retrying failed order {order_id}, attempt {rec['attempts']}"
                )
                # resubmit
                new_oid = self.submit_signal(rec["signal"])
                logger.info(f"Resubmitted order as {new_oid}")
                # mark old as replaced
                rec["status"] = "replaced"
                return True
            else:
                rec["status"] = "failed"
                logger.error(f"Order permanently failed after retries: {order_id}")
                return False

        if status == "canceled":
            rec["status"] = "canceled"
            logger.info(f"Order canceled: {order_id}")
            return True

        logger.info(f"Unhandled receipt status {status} for {order_id}")
        return False

    def set_paper_mode(self, paper: bool):
        self.paper_mode = bool(paper)
