# -*- coding: utf-8 -*-
"""
Application initializer: loads config, sets up logging and core services
"""
import json
import logging
import os
from logging.handlers import RotatingFileHandler

from src.data.data_storage import DataStorage
from src.data.data_provider import DataProvider
from src.strategies.gemini_agent import GeminiAgent
from src.utils.notifier import DingTalkNotifier
from src.trading.trade_executor import TradeExecutor
from src.trading.scheduler import Scheduler


class App:
    def __init__(
        self,
        config_path: str = "config.json",
        mode: str = "paper",
        dry_run: bool = False,
    ):
        self.config_path = config_path
        self.mode = mode
        self.dry_run = dry_run
        raw_cfg = self._load_config(config_path)
        self.config = self._normalize_config(raw_cfg)
        self._ensure_paths()
        self.logger = self._init_logging()

        # Core services
        self.storage = DataStorage(
            db_path=self.config["paths"]["db_path"],
            data_path=self.config["paths"]["data_path"],
        )
        self.data_provider = DataProvider(self.storage)
        self.gemini = GeminiAgent(api_key=self.config["api_keys"].get("gemini_api_key"))
        self.notifier = DingTalkNotifier(
            token=self.config["api_keys"].get("dingtalk_token")
        )
        self.trader = TradeExecutor(
            account_id=self.config["account"]["qmt_account_id"],
            mini_qmt_path=self.config["account"]["mini_qmt_path"],
            max_drawdown=self.config["strategy"].get("max_drawdown", 0.2),
        )
        self.scheduler = Scheduler()
        # Order manager
        from src.trading.order_manager import OrderManager

        self.order_manager = OrderManager(
            self.trader,
            max_retries=self.config.get("system", {}).get("order_max_retries", 3),
            retry_delay=self.config.get("system", {}).get("order_retry_delay", 2),
            paper_mode=self.dry_run or (self.mode != "live"),
        )

        # Risk manager
        from src.risk.risk_manager import RiskManager

        self.risk_manager = RiskManager(
            self.trader,
            storage=self.storage,
            max_drawdown=self.config.get("strategy", {}).get("max_drawdown", 0.2),
            max_position_pct=self.config.get("strategy", {}).get(
                "max_position_pct", 0.1
            ),
            max_position_per_symbol=self.config.get("strategy", {}).get(
                "max_position_per_symbol", 100000
            ),
        )
        # Inject into order manager
        self.order_manager.risk_manager = self.risk_manager

        # Strategy placeholder (constructed lazily or by factory)
        self.strategy = None

    def _normalize_config(self, raw_cfg: dict) -> dict:
        """Normalize older/newer config variants into a consistent shape used by App."""
        cfg = dict(raw_cfg) if isinstance(raw_cfg, dict) else {}
        # Paths
        paths = cfg.get("paths", {})
        if not paths:
            # Support older config that used 'db' and 'qmt'
            db_cfg = cfg.get("db", {})
            paths["db_path"] = db_cfg.get("sqlite_path", "db/quant.db")
            paths["data_path"] = cfg.get("paths", {}).get("data_path", "db/market_data")
            paths["log_path"] = cfg.get("paths", {}).get("log_path", "logs")
        else:
            paths.setdefault("db_path", "db/quant.db")
            paths.setdefault("data_path", "db/market_data")
            paths.setdefault("log_path", "logs")

        # Account
        account = cfg.get("account", {})
        if not account:
            qmt = cfg.get("qmt", {})
            account["mini_qmt_path"] = qmt.get("shortcut_path", "")
            account["qmt_account_id"] = qmt.get("account_id", "")
            account.setdefault("account_type", "STOCK")
        else:
            account.setdefault("mini_qmt_path", "")
            account.setdefault("qmt_account_id", "")
            account.setdefault("account_type", "STOCK")

        # Strategy
        strategy = cfg.get("strategy", {})
        strategy.setdefault("active_strategies", strategy.get("active_strategies", []))
        strategy.setdefault("max_drawdown", strategy.get("max_drawdown", 0.2))
        strategy.setdefault("stocks_pool", strategy.get("stocks_pool", []))

        # API keys
        api_keys = cfg.get("api_keys", {})
        api_keys.setdefault("gemini_api_key", cfg.get("gemini_api_key"))
        api_keys.setdefault("dingtalk_token", cfg.get("dingtalk_token"))

        # System
        system = cfg.get("system", {})
        system.setdefault("log_level", system.get("log_level", "INFO"))

        return {
            "paths": paths,
            "account": account,
            "strategy": strategy,
            "api_keys": api_keys,
            "system": system,
        }

    def _load_config(self, path: str) -> dict:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _ensure_paths(self):
        # Ensure log and data directories exist
        paths = self.config.get("paths", {})
        log_path = paths.get("log_path", "logs")
        data_path = paths.get("data_path", "db/market_data")
        os.makedirs(log_path, exist_ok=True)
        os.makedirs(data_path, exist_ok=True)

    def _init_logging(self):
        cfg = self.config.get("system", {})
        level = getattr(logging, cfg.get("log_level", "INFO").upper(), logging.INFO)
        log_dir = self.config.get("paths", {}).get("log_path", "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "app.log")

        logger = logging.getLogger("quant_app")
        logger.setLevel(level)
        if not logger.handlers:
            fh = RotatingFileHandler(
                log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
            )
            fh.setLevel(level)
            fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
            fh.setFormatter(fmt)
            logger.addHandler(fh)

            sh = logging.StreamHandler()
            sh.setLevel(level)
            sh.setFormatter(fmt)
            logger.addHandler(sh)

        logger.debug(f"Logger initialized (level={logging.getLevelName(level)})")
        return logger

    def build_strategy(self):
        # Simple factory: pick first configured strategy or fallback
        active = self.config.get("strategy", {}).get("active_strategies", [])
        name = active[0] if active else None
        if not name:
            self.logger.warning(
                "No active strategy configured; using TopGainerStrategy by default"
            )
            from src.strategies.top_gainer_strategy import TopGainerStrategy

            self.strategy = TopGainerStrategy(
                "TopGainer_v1", self.config["strategy"], self.gemini
            )
            return self.strategy

        # Try to find a matching strategy by name
        try:
            # Try direct import convention: src.strategies.<lower>_strategy
            mod_name = f"src.strategies.{name.lower()}_strategy"
            mod = __import__(mod_name, fromlist=["*"])
            # Find a class that endswith 'Strategy' and contains the name
            for attr in dir(mod):
                if attr.lower().endswith("strategy") and name.lower() in attr.lower():
                    cls = getattr(mod, attr)
                    self.strategy = (
                        cls(name, self.config["strategy"], self.gemini)
                        if callable(cls)
                        else None
                    )
                    break

        except Exception:
            self.logger.warning(
                f"Could not import configured strategy module for '{name}', "
                "falling back to TopGainerStrategy"
            )

        if not self.strategy:
            from src.strategies.top_gainer_strategy import TopGainerStrategy

            self.strategy = TopGainerStrategy(
                "TopGainer_v1", self.config["strategy"], self.gemini
            )

        self.logger.info(f"Using strategy: {self.strategy.__class__.__name__}")
        return self.strategy

    def schedule_paper_run(
        self,
        minutes: int = 60,
        rounds: int = 1,
        stocks: list = None,
        report_path: str = "reports/paper_run.json",
    ):
        """Schedule a periodic paper-run job using the internal Scheduler."""
        from scripts.paper_run import run_paper

        def job():
            try:
                self.logger.info(
                    f"Scheduled paper run starting: rounds={rounds}, stocks={stocks}"
                )
                run_paper(
                    config_path=self.config_path,
                    rounds=rounds,
                    stocks=stocks
                    or self.config.get("strategy", {}).get("stocks_pool", []),
                    report_path=report_path,
                )
                self.logger.info("Scheduled paper run completed")
            except Exception as e:
                self.logger.exception(f"Error running scheduled paper run: {e}")

        # register job
        self.scheduler.add_interval_job(minutes, job)
        self.logger.info(f"Paper-run scheduled every {minutes} minutes")
        return True

    def start_trader_if_needed(self):
        # Start trader unless in backtest or dry-run
        if self.mode == "backtest" or self.dry_run:
            self.logger.info("Running in backtest/dry-run mode; trading disabled.")
            return False

        started = self.trader.start()
        if started:
            self.logger.info("Trader started and connected.")
            # In live mode, start the receipt listener to handle async fills
            if self.mode == "live":
                poll = self.config.get("system", {}).get("receipt_poll_interval", 1.0)
                try:
                    self.trader.start_receipt_listener(poll_interval=poll)
                    self.logger.info("Receipt listener started for live trading")
                except Exception as e:
                    self.logger.exception(f"Failed starting receipt listener: {e}")
        else:
            self.logger.warning(
                "Trader failed to connect; running in observation mode."
            )
        return started

    def shutdown(self):
        try:
            # Stop receipt listener if running
            try:
                self.trader.stop_receipt_listener()
            except Exception:
                pass
            self.trader.stop()
        except Exception:
            pass
        self.logger.info("App shutdown completed.")
