# -*- coding: utf-8 -*-
"""Simple RiskManager that enforces position limits and drawdown rules.
This is intentionally lightweight and unit-test friendly.
"""
from dataclasses import dataclass
import logging
from typing import Optional

logger = logging.getLogger("quant_app.risk")


@dataclass
class AssetSnapshot:
    total_asset: float


class RiskManager:
    def __init__(
        self,
        trader,
        storage=None,
        max_drawdown: float = 0.2,
        max_position_pct: float = 0.1,
        max_position_per_symbol: int = 100000,
    ):
        """Initialize risk manager.

        - trader: object exposing get_assets() -> object with .total_asset
        - storage: optional DB/storage to persist risk decisions
        - max_drawdown: fraction (e.g., 0.2 for 20%)
        - max_position_pct: maximum fraction of equity allowed per symbol
        - max_position_per_symbol: absolute share quantity limit per symbol
        """
        self.trader = trader
        self.storage = storage
        self.max_drawdown = float(max_drawdown)
        self.max_position_pct = float(max_position_pct)
        self.max_position_per_symbol = int(max_position_per_symbol)

        # snapshot initial equity
        self.initial_equity = self._get_total_asset() or 0.0

        # In-memory positions: {code: qty}
        self.positions = {}

    def _get_total_asset(self) -> Optional[float]:
        try:
            assets = self.trader.get_assets()
            if assets and hasattr(assets, "total_asset"):
                return float(assets.total_asset)
        except Exception:
            pass
        return None

    def get_current_equity(self) -> float:
        val = self._get_total_asset()
        if val is None:
            return self.initial_equity
        return val

    def check_order(self, signal: dict) -> (bool, str):
        """Check if order passes risk rules.

        Returns (ok: bool, reason: str)
        """
        code = signal.get("code")
        vol = int(signal.get("volume", 0))
        typ = signal.get("signal_type", "").upper()

        # Basic checks
        if vol <= 0:
            return False, "zero_volume"

        # per-symbol hard limit
        existing = abs(self.positions.get(code, 0))
        if existing + vol > self.max_position_per_symbol:
            return False, "exceeds_symbol_limit"

        # Check max position percent vs current equity, need an estimated price
        price = float(signal.get("price", 0) or 0)
        equity = self.get_current_equity() or self.initial_equity
        if equity <= 0:
            return False, "no_equity_info"

        # risk cash usage
        order_value = vol * price
        if order_value / equity > self.max_position_pct:
            return False, "exceeds_position_pct"

        # drawdown check: simulate instant change in equity if needed (conservative: do not allow if drawdown already exceeded)
        current_equity = self.get_current_equity()
        if self.initial_equity and current_equity / self.initial_equity < (
            1 - self.max_drawdown
        ):
            return False, "max_drawdown_exceeded"

        return True, "ok"

    def apply_trade_effect(self, code: str, qty: int):
        """Apply a matched fill to internal positions tracking (qty positive for buy)."""
        self.positions[code] = self.positions.get(code, 0) + int(qty)
        logger.info(f"Position updated: {code} -> {self.positions[code]}")

    def set_initial_equity(self, amount: float):
        self.initial_equity = float(amount)

    def reset(self):
        self.positions = {}
