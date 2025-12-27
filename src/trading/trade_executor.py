# -*- coding: utf-8 -*-
import time
from xtquant import xttrader, xtconstant
from xtquant.xttype import StockAccount

class TradeExecutor:
    def __init__(self, account_id, mini_qmt_path, max_drawdown=0.2):
        self.account_id = account_id
        self.mini_qmt_path = mini_qmt_path
        self.max_drawdown = max_drawdown
        self.session_id = int(time.time())
        
        self.xt_trader = xttrader.XtQuantTrader(mini_qmt_path, self.session_id)
        self.account = StockAccount(account_id)
        
        self.initial_equity = None

        # receipt handlers: functions that accept (order_id, status, info)
        self._receipt_handlers = []

    def register_receipt_handler(self, fn):
        """Register a callback to receive order receipts (order_id, status, info)."""
        if callable(fn):
            self._receipt_handlers.append(fn)

    def _emit_receipt(self, order_id, status, info=None):
        for h in list(self._receipt_handlers):
            try:
                h(order_id, status, info)
            except Exception:
                # handler errors should not kill the executor
                try:
                    import traceback
                    traceback.print_exc()
                except Exception:
                    pass

    # helper for tests / simulation to inject receipts
    def simulate_receipt(self, order_id, status, info=None):
        self._emit_receipt(order_id, status, info)

        # receipt listener placeholder
        self.receipt_listener = None

    def start_receipt_listener(self, poll_interval: float = 1.0, fetch_func=None):
        """Start background receipt listener to forward receipts to OrderManager."""
        try:
            from src.trading.receipt_listener import ReceiptListener
            if self.receipt_listener is None:
                self.receipt_listener = ReceiptListener(self, poll_interval=poll_interval, fetch_func=fetch_func)
                self.receipt_listener.start()
        except Exception:
            # Keep tolerant if environment doesn't support listener
            import traceback
            traceback.print_exc()

    def stop_receipt_listener(self):
        if getattr(self, 'receipt_listener', None):
            try:
                self.receipt_listener.stop()
            except Exception:
                pass
            self.receipt_listener = None
        
    def start(self):
        """Connect to QMT and start trading session."""
        self.xt_trader.start()
        res = self.xt_trader.connect()
        if res == 0:
            self.xt_trader.subscribe(self.account)
            # Record initial equity for risk check
            assets = self.get_assets()
            if assets:
                self.initial_equity = assets.total_asset
            return True
        return False

    def get_assets(self):
        """Get current account assets."""
        return self.xt_trader.query_stock_asset(self.account)

    def check_risk_ok(self):
        """
        Check if current drawdown exceeds limit.
        """
        if self.initial_equity is None:
            return True # Not initialized yet
        
        assets = self.get_assets()
        if not assets:
            return False # Conservative
            
        current_equity = assets.total_asset
        drawdown = 1.0 - (current_equity / self.initial_equity)
        
        if drawdown > self.max_drawdown:
            print(f"RISK ALERT: Max drawdown reached ({drawdown*100:.2f}%). Trading halted.")
            return False
        
        return True

    def execute_signal(self, signal):
        """
        Execute a trading signal.
        signal: dict with 'code', 'signal_type' (BUY/SELL), 'price', 'volume'
        """
        if not self.check_risk_ok():
            return "RISK_HALT"

        code = signal.get('code')
        volume = int(signal.get('volume', 100))
        price = float(signal.get('price', 0))
        signal_type = signal.get('signal_type', '').upper()
        
        action_type = xtconstant.STOCK_BUY if signal_type == 'BUY' else xtconstant.STOCK_SELL
        
        # Simple order (FIX Price)
        order_id = self.xt_trader.order_stock(
            self.account,
            code,
            action_type,
            volume,
            xtconstant.FIX_PRICE,
            price,
            signal.get('source', 'auto'),
            signal.get('source', 'auto')
        )
        
        return order_id

    def stop(self):
        self.xt_trader.stop()
