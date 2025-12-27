# -*- coding: utf-8 -*-
"""运行回测示例：加载 features parquet，生成信号并运行 SimpleBacktester"""
import os
import pandas as pd
from src.backtest.backtester import SimpleBacktester
from src.strategies.momentum import ma_crossover_signal

p = 'db/market_data/600000.SH_1d.features.parquet'
if not os.path.exists(p):
    print('features not found, please run scripts/test_preprocess.py first')
    raise SystemExit(1)

print('loading features', p)
df = pd.read_parquet(p)
print('rows', len(df))
signal = ma_crossover_signal(df, short=5, long=20)

bt = SimpleBacktester(initial_cash=100000)
res = bt.run(df[['open','high','low','close']], signal)
print('total_return', res.total_return)
print('annual_return', res.annual_return)
print('max_drawdown', res.max_drawdown)
print('sharpe', res.sharpe)
# save equity curve for inspection
out = 'results/600000_equity.csv'
os.makedirs('results', exist_ok=True)
res.equity.to_csv(out)
print('equity saved to', out)
