# -*- coding: utf-8 -*-
import time
import random
from xtquant import xttrader
from xtquant.xttype import StockAccount
from xtquant import xtconstant

class TradeManager:
    def __init__(self, account_id, mini_qmt_path):
        self.account_id = account_id
        # Session ID is random to distinguish connections
        self.session_id = int(time.time())
        self.xt_trader = xttrader.XtQuantTrader(mini_qmt_path, self.session_id)
        # Assuming STOCK account type for A-shares
        self.account = StockAccount(account_id)
        
        # Callback for connection status
        self.xt_trader.register_callback(self)


    def connect(self):
        """
        Connect to MiniQMT Client.
        """
        print(f"Connecting to MiniQMT with account: {self.account_id}...")
        self.xt_trader.start()
        
        # Establishing connection
        connect_result = self.xt_trader.connect()
        if connect_result == 0:
            print("Connection successful.")
            # Subscribe to account updates
            subscribe_result = self.xt_trader.subscribe(self.account)
            if subscribe_result == 0:
                print("Subscribed to account updates.")
            else:
                print(f"Failed to subscribe to account: {subscribe_result}")
            return True
        else:
            print(f"Connection failed with code: {connect_result}")
            return False

    def buy(self, stock_code, price, volume, strategy_name='auto_strategy', order_remark='buy_order'):
        """
        Place a buy order.
        """
        print(f"Placing BUY order: {stock_code}, Price: {price}, Volume: {volume}")
        return self.xt_trader.order_stock(
            self.account,
            stock_code,
            xtconstant.STOCK_BUY, 
            int(volume),
            xtconstant.FIX_PRICE, 
            float(price),
            strategy_name,
            order_remark
        )

    def sell(self, stock_code, price, volume, strategy_name='auto_strategy', order_remark='sell_order'):
        """
        Place a sell order.
        """
        print(f"Placing SELL order: {stock_code}, Price: {price}, Volume: {volume}")
        return self.xt_trader.order_stock(
            self.account,
            stock_code,
            xtconstant.STOCK_SELL, 
            int(volume),
            xtconstant.FIX_PRICE, 
            float(price),
            strategy_name,
            order_remark
        )

    def get_assets(self):
        """
        Query account assets.
        """
        assets = self.xt_trader.query_stock_asset(self.account)
        if assets:
            print(f"Cash: {assets.cash}, Market Value: {assets.market_value}")
        return assets
    
    def on_connected(self):
        """
        Callback when connected.
        """
        print("Callback: Connected to XtQuantTrader.")
    
    def on_disconnected(self):
        """
        Callback when disconnected.
        """
        print("Callback: Disconnected from XtQuantTrader.")

    def on_stock_order(self, order):
        """
        Callback for order updates.
        """
        print(f"Order Update: {order.order_id}, Status: {order.order_status}")

    def on_stock_trade(self, trade):
        """
        Callback for trade execution.
        """
        print(f"Trade Executed: {trade.stock_code}, Price: {trade.traded_price}, Volume: {trade.traded_volume}")
