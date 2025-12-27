# -*- coding: utf-8 -*-
from .strategy_base import StrategyBase
import pandas as pd


class BreakoutStrategy(StrategyBase):
    """突破策略：当价格突破过去 N 日最高价（向上突破）则买入；跌破过去 N 日最低价则平仓（或反向）。"""

    def __init__(self, lookback=20, name=None):
        super().__init__(strategy_name=name or 'Breakout', config_params={'lookback': lookback})
        self.lookback = lookback

    def generate_signals(self, price_df: pd.DataFrame) -> pd.Series:
        df = price_df.copy()
        high = df['high']
        low = df['low']
        close = df['close']

        rolling_high = high.shift(1).rolling(self.lookback, min_periods=1).max()
        rolling_low = low.shift(1).rolling(self.lookback, min_periods=1).min()

        signal = pd.Series(0, index=df.index)
        pos = 0
        for idx in df.index:
            if pos == 0 and close.loc[idx] > rolling_high.loc[idx]:
                pos = 1
            elif pos == 1 and close.loc[idx] < rolling_low.loc[idx]:
                pos = 0
            signal.loc[idx] = pos
        return signal
