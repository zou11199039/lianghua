# -*- coding: utf-8 -*-
import pandas as pd
from src.strategies.mean_reversion import MeanReversionStrategy


def test_mean_reversion_signal_length():
    dates = pd.date_range("2020-01-01", periods=30, freq="D")
    prices = pd.Series(range(30), index=dates).astype(float)
    df = pd.DataFrame({"open": prices, "high": prices, "low": prices, "close": prices})
    strat = MeanReversionStrategy(window=5, z_entry=1.0, z_exit=0.5)
    sig = strat.generate_signals(df)
    assert len(sig) == len(df)
    assert set(sig.unique()).issubset({0, 1})
