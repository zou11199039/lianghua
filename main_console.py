# -*- coding: utf-8 -*-
import sys
import time
import argparse
from src.core.app import App


class ConsoleSystem:
    """Console wrapper that uses the central App initializer."""

    def __init__(self, app: App):
        self.app = app
        self.config = app.config
        self.logger = app.logger
        self.running = False

        self.storage = app.storage
        self.data_provider = app.data_provider
        self.strategy = app.strategy or app.build_strategy()
        self.trader = app.trader
        self.notifier = app.notifier

        self.logger.info("Console System initialized.")

    def log(self, msg):
        self.logger.info(msg)

    def log(self, msg):
        # Keep simple console echo for interactive mode but prefer structured logs
        self.logger.info(msg)

    def health_check(self):
        """Simple health check: storage accessible and trader connection state"""
        ok = True
        try:
            _ = self.storage
        except Exception as e:
            self.logger.error(f"Storage health check failed: {e}")
            ok = False
        return ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the console trading system")
    parser.add_argument(
        "--config", "-c", default="config.json", help="Path to config file"
    )
    parser.add_argument(
        "--mode", choices=["backtest", "paper", "live"], default="paper"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Disable any real trading"
    )
    args = parser.parse_args()

    app = App(config_path=args.config, mode=args.mode, dry_run=args.dry_run)
    app.build_strategy()
    app.start_trader_if_needed()

    system = ConsoleSystem(app)
    system.run()

    def run_strategy_logic(self):
        """Core logic"""
        self.log(f"--- Running Strategy Route ---")

        try:
            # 1. Update Data
            stock_list = self.config["strategy"]["stocks_pool"]
            if not stock_list:
                self.log("Warning: Stock pool is empty in config.")
                return

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
                    self.notifier.send_text(
                        f"Order Executed: {sig['code']} {sig['signal_type']} @ {sig['price']}"
                    )
                elif order_id == "RISK_HALT":
                    self.log("Order rejected by Risk Manager.")

        except Exception as e:
            self.log(f"Error in strategy loop: {e}")
            import traceback

            traceback.print_exc()

    def run(self):
        self.log("System Started.")

        # Connect Trader
        if self.trader.start():
            self.log("Connected to QMT Trading successfully.")
        else:
            self.log(
                "Failed to connect to QMT. Running in OBSERVATION MODE (No Trading)."
            )
            self.log("Please ensure MiniQMT client is running and logged in.")

        self.running = True
        try:
            while self.running:
                cmd = input("\n[Command] (r: run strategy, q: quit) > ").strip().lower()

                if cmd == "r":
                    self.run_strategy_logic()
                elif cmd == "q":
                    self.running = False
                    break
                else:
                    print("Unknown command.")

        except KeyboardInterrupt:
            pass

        self.trader.stop()
        self.log("System Stopped.")


if __name__ == "__main__":
    system = ConsoleSystem()
    system.run()
