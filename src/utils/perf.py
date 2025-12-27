# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np


def max_drawdown(returns: pd.Series) -> float:
    cum = (1 + returns).cumprod()
    peak = cum.cummax()
    drawdown = (cum - peak) / peak
    return float(drawdown.min())


def annual_return(returns: pd.Series, days: int) -> float:
    total = (1 + returns).prod() - 1
    return float((1 + total) ** (252 / max(days, 1)) - 1)


def sharpe(returns: pd.Series) -> float:
    if returns.std() == 0:
        return 0.0
    return float((returns.mean() / returns.std()) * np.sqrt(252))
