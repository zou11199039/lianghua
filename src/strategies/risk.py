# -*- coding: utf-8 -*-
import pandas as pd


def apply_stop_take(
    price_df: pd.DataFrame,
    signal: pd.Series,
    stop_loss: float = 0.05,
    take_profit: float = 0.1,
) -> pd.Series:
    """给定原始 signal（0/1），在持仓期间检查是否触发止损/止盈（基于持仓开仓时的成本价，使用 high/low 作为触发价格）。
    返回修改后的 signal（0/1），当触发止损/止盈当天会平仓（signal=0）。
    注意：此实现为简化版本，适用于日频回测。
    """
    df = price_df.copy()
    out_signal = signal.copy().astype(int)

    position = 0
    entry_price = None

    for idx in df.index:
        cur_signal = int(signal.loc[idx])
        close = df.loc[idx, "close"]
        high = df.loc[idx, "high"]
        low = df.loc[idx, "low"]

        # entry
        if position == 0 and cur_signal == 1:
            position = 1
            entry_price = close
            out_signal.loc[idx] = 1
            continue

        if position == 1:
            # check take profit first
            if take_profit is not None and (high >= entry_price * (1 + take_profit)):
                # take profit triggered -> close position
                position = 0
                out_signal.loc[idx] = 0
                entry_price = None
                continue
            # check stop loss
            if stop_loss is not None and (low <= entry_price * (1 - stop_loss)):
                position = 0
                out_signal.loc[idx] = 0
                entry_price = None
                continue
            # if signal says exit, exit
            if cur_signal == 0:
                position = 0
                out_signal.loc[idx] = 0
                entry_price = None
                continue
            # otherwise keep position
            out_signal.loc[idx] = 1
        else:
            out_signal.loc[idx] = 0

    return out_signal
