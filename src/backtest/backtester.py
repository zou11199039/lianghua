# -*- coding: utf-8 -*-
"""
简易回测框架（适合日频回测与策略验证）
功能：
- 根据 signal（1=long, 0=flat）在下一个交易日开盘价执行买入/卖出
- 支持仓位限制、滑点、手续费
- 计算回测指标：净值曲线、累计收益、年化收益（简单）、最大回撤、夏普比率
"""
from dataclasses import dataclass
import pandas as pd
import numpy as np


@dataclass
class BacktestResult:
    equity: pd.Series
    returns: pd.Series
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe: float


class SimpleBacktester:
    def __init__(self, initial_cash=1_000_000, commission=0.0005, slippage=0.001):
        self.initial_cash = initial_cash
        self.commission = commission
        self.slippage = slippage

    def run(self, price_df: pd.DataFrame, signal: pd.Series) -> BacktestResult:
        """price_df must contain columns: open, high, low, close and have DatetimeIndex.
        signal is a series aligned with index with values in {0,1} (long or flat)
        We assume for simplicity: when signal changes from 0->1 we buy at next open price, on 1->0 we sell at next open price.
        """
        df = price_df.copy().sort_index()
        s = signal.reindex(df.index).fillna(0).astype(int)

        cash = self.initial_cash
        position = 0.0  # number of shares
        equity = []
        prev_signal = 0

        for i, idx in enumerate(df.index):
            row = df.loc[idx]
            next_open = row['open']  # use today's open as execution (detailed simulation could use next day's open)

            cur_signal = s.loc[idx]
            # Entry
            if prev_signal == 0 and cur_signal == 1:
                # buy as much as possible with full cash
                # avoid fractional shares for realism
                price = next_open * (1 + self.slippage)
                qty = int((cash / (price * (1 + self.commission))))
                cost = qty * price * (1 + self.commission)
                if qty > 0:
                    position = qty
                    cash -= cost
            # Exit
            elif prev_signal == 1 and cur_signal == 0:
                if position > 0:
                    price = next_open * (1 - self.slippage)
                    proceeds = position * price * (1 - self.commission)
                    cash += proceeds
                    position = 0

            # mark-to-market equity
            mkt_val = position * row['close']
            total_equity = cash + mkt_val
            equity.append((idx, total_equity))

            prev_signal = cur_signal

        equity_idx = pd.Series([v for (_, v) in equity], index=[i for (i, _) in equity])
        returns = equity_idx.pct_change().fillna(0)
        total_return = equity_idx.iloc[-1] / equity_idx.iloc[0] - 1
        # approx annual return assuming 252 trading days per year
        days = (equity_idx.index[-1] - equity_idx.index[0]).days if len(equity_idx.index) > 1 else 1
        annual_return = (1 + total_return) ** (252 / max(days, 1)) - 1
        # max drawdown
        cum = (1 + returns).cumprod()
        peak = cum.cummax()
        drawdown = (cum - peak) / peak
        max_drawdown = drawdown.min()
        # sharpe (assume 0 risk-free) annualized
        if returns.std() == 0:
            sharpe = 0.0
        else:
            sharpe = (returns.mean() / returns.std()) * np.sqrt(252)

        return BacktestResult(equity=equity_idx, returns=returns, total_return=float(total_return), annual_return=float(annual_return), max_drawdown=float(max_drawdown), sharpe=float(sharpe))
