# -*- coding: utf-8 -*-
import sys
import json
import time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal

# Import Modules
from src.data.data_storage import DataStorage
from src.data.data_provider import DataProvider
from src.strategies.gemini_agent import GeminiAgent
from src.strategies.top_gainer_strategy import TopGainerStrategy
from src.trading.trade_executor import TradeExecutor
from src.trading.scheduler import Scheduler
from src.utils.notifier import DingTalkNotifier
from src.ui.main_window import MainWindow

class SystemBackend(QThread):
    msg_signal = pyqtSignal(str)

    def __init__(self, app_config_path='config.json'):
        super().__init__()
        # Use centralized App initializer for consistency
        from src.core.app import App
        self.app = App(config_path=app_config_path, mode='paper', dry_run=False)
        self.config = self.app.config
        self.running = False
        self.manual_trigger = False

        # Expose services for the UI
        self.storage = self.app.storage
        self.data_provider = self.app.data_provider
        self.gemini = self.app.gemini
        self.strategy = self.app.strategy or self.app.build_strategy()
        self.trader = self.app.trader
        self.notifier = self.app.notifier
        self.scheduler = self.app.scheduler

    def _load_config(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def log(self, msg):
        self.msg_signal.emit(msg)
        print(msg) # console fallback

    def run_strategy_logic(self):
        """Core logic: Data -> Strategy -> Signal -> Risk -> Trade"""
        self.log(f"--- Running Strategy Route ---")
        
        try:
            # 1. Update Data
            stock_list = self.config['strategy']['stocks_pool']
            self.log(f"Updating data for {len(stock_list)} stocks...")
            self.data_provider.download_data(stock_list)
            kline_data = self.data_provider.get_kline(stock_list)
            
            # 2. Strategy Analysis
            self.log("Analyzing market...")
            signals = self.strategy.on_market_data(None, kline_data)
            self.log(f"Signals generated: {len(signals)}")
            
            # 3. Execution
            for sig in signals:
                self.log(f"Processing signal: {sig}")
                # Log to DB
                self.storage.log_signal(sig)
                
                # Check Risk & Execute
                order_id = self.trader.execute_signal(sig)
                
                if order_id and order_id != "RISK_HALT":
                    self.log(f"Order placed. ID: {order_id}")
                    # Notify
                    self.notifier.send_text(f"Order Executed: {sig['code']} {sig['signal_type']} @ {sig['price']}")
                elif order_id == "RISK_HALT":
                    self.log("Order rejected by Risk Manager.")
                    
        except Exception as e:
            self.log(f"Error in strategy loop: {e}")
            import traceback
            self.log(traceback.format_exc())

    def run(self):
        self.log("Backend System Started.")
        
        # Connect Trader
        if self.trader.start():
            self.log("Connected to QMT Trading.")
        else:
            self.log("Failed to connect to QMT. Running in Observation Mode.")

        # Schedule jobs
        # self.scheduler.add_daily_job("09:30", self.run_strategy_logic)
        
        self.running = True
        while self.running:
            if self.manual_trigger:
                self.run_strategy_logic()
                self.manual_trigger = False
            
            time.sleep(1)
            
        self.trader.stop()
        self.log("Backend System Stopped.")

    def stop(self):
        self.running = False
        self.wait()

    def trigger_strategy(self):
        self.manual_trigger = True


def main():
    app = QApplication(sys.argv)
    
    # Init GUI
    window = MainWindow()
    
    # Init Backend
    backend = SystemBackend()
    
    # Signals wiring
    backend.msg_signal.connect(window.log)
    
    # UI Control wiring
    window.btn_start.clicked.connect(backend.start)
    window.btn_stop.clicked.connect(backend.stop)
    window.btn_run_strategy.clicked.connect(backend.trigger_strategy)
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
