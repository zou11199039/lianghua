# -*- coding: utf-8 -*-
from .strategy_base import StrategyBase
import pandas as pd


class MeanReversionStrategy(StrategyBase):
    """基于 z-score 的均值回归策略。

    当价格与均线的 z-score 超出阈值时产生信号。
    由于 A 股不可做空，此策略采用长/平逻辑：价格低于均值超过阈值时买入，价格高于均值超过阈值时平仓。
    """

    def __init__(self, window=20, z_entry=1.5, z_exit=0.5, name=None):
        super().__init__(
            strategy_name=name or "MeanReversion",
            config_params={"window": window, "z_entry": z_entry, "z_exit": z_exit},
        )
        self.window = window
        self.z_entry = z_entry
        self.z_exit = z_exit

    def generate_signals(self, price_df: pd.DataFrame) -> pd.Series:
        df = price_df.copy()
        close = df["close"]
        ma = close.rolling(self.window, min_periods=1).mean()
        std = close.rolling(self.window, min_periods=1).std().replace(0, 1e-8)
        z = (close - ma) / std

        # signal: 1 -> long, 0 -> flat
        signal = pd.Series(0, index=df.index)
        long_cond = z <= -self.z_entry  # price sufficiently below mean
        exit_cond = z >= -self.z_exit

        pos = 0
        for idx in df.index:
            if pos == 0 and long_cond.loc[idx]:
                pos = 1
            elif pos == 1 and exit_cond.loc[idx]:
                pos = 0
            signal.loc[idx] = pos

        return signal

    def on_init(self):
        # No stateful initialization required for this simple strategy
        return None

    def on_market_data(self, market_df):
        # For backtest/live hook: return the latest signal series
        return self.generate_signals(market_df)
