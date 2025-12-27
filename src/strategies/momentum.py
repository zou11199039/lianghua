# -*- coding: utf-8 -*-
"""
简单的动量策略：短期均线突破长期均线产生买入信号
"""
import pandas as pd


def ma_crossover_signal(df: pd.DataFrame, short: int = 5, long: int = 20) -> pd.Series:
    df = df.copy()
    df["ma_s"] = df["close"].rolling(short, min_periods=1).mean()
    df["ma_l"] = df["close"].rolling(long, min_periods=1).mean()
    signal = (df["ma_s"] > df["ma_l"]).astype(int)
    # Ensure the signal is forward-looking by shifting if needed.
    # (Here we execute at the open same day for simplicity.)
    return signal
