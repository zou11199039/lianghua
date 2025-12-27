# -*- coding: utf-8 -*-
"""简单回测单元测试脚本（非自动化的 pytest，用于手动验证）"""
import pandas as pd
import numpy as np
from src.backtest.backtester import SimpleBacktester

# 构造简单价格序列：上升趋势
dates = pd.date_range("2020-01-01", periods=100, freq="D")
prices = pd.Series(np.linspace(10, 20, len(dates)), index=dates)
df = pd.DataFrame(
    {"open": prices, "high": prices * 1.01, "low": prices * 0.99, "close": prices}
)
# 信号：一直持有
signal = pd.Series(1, index=dates)

bt = SimpleBacktester(initial_cash=100000)
res = bt.run(df, signal)
print("total_return", res.total_return)
print("annual_return", res.annual_return)
print("max_drawdown", res.max_drawdown)
print("sharpe", res.sharpe)
assert res.total_return > 0
print("test_backtest passed")
