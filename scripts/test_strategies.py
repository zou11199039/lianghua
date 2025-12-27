# -*- coding: utf-8 -*-
"""测试策略库：运行均值回归与突破策略并进行回测，输出主要指标"""
import os
import pandas as pd
from src.strategies.mean_reversion import MeanReversionStrategy
from src.strategies.breakout import BreakoutStrategy
from src.strategies.risk import apply_stop_take
from src.backtest.backtester import SimpleBacktester


def run_strategy_test(code='600000.SH', period='1d'):
    feat_path = f'db/market_data/{code}_{period}.features.parquet'
    if not os.path.exists(feat_path):
        print('features file not found:', feat_path)
        print('Please run scripts/test_preprocess.py first')
        return

    df = pd.read_parquet(feat_path)

    strategies = [MeanReversionStrategy(window=20, z_entry=1.5, z_exit=0.5), BreakoutStrategy(lookback=20)]

    for strat in strategies:
        print('\n=== Running strategy', strat)
        sig = strat.generate_signals(df)
        # apply stoploss/takeprofit for realism
        sig2 = apply_stop_take(df, sig, stop_loss=0.05, take_profit=0.1)
        bt = SimpleBacktester(initial_cash=100000)
        res = bt.run(df[['open','high','low','close']], sig2)
        print('total_return', res.total_return)
        print('annual_return', res.annual_return)
        print('max_drawdown', res.max_drawdown)
        print('sharpe', res.sharpe)


if __name__ == '__main__':
    run_strategy_test()
