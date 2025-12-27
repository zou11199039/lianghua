# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from src.strategies.risk import apply_stop_take


def test_apply_stop_take_triggers():
    dates = pd.date_range('2020-01-01', periods=5, freq='D')
    # price rises then drops to trigger stop loss
    df = pd.DataFrame({'open':[10,11,12,11,8],'high':[10,11,12,11,9],'low':[10,10.5,11.5,8,7.5],'close':[10,11,12,9,8]}, index=dates)
    # always long
    sig = pd.Series(1, index=dates)
    out = apply_stop_take(df, sig, stop_loss=0.1, take_profit=0.2)
    # expect exit when low <= entry*(1-stop_loss) -> entry =10, stop at <=9
    assert out.iloc[3] == 0 or out.iloc[4] == 0


def test_apply_stop_take_no_trigger():
    dates = pd.date_range('2020-02-01', periods=4, freq='D')
    df = pd.DataFrame({'open':[10,10.5,10.8,11],'high':[10.5,10.8,11,11.2],'low':[9.8,10,10.5,10.7],'close':[10,10.6,10.7,11]}, index=dates)
    sig = pd.Series(1, index=dates)
    out = apply_stop_take(df, sig, stop_loss=0.2, take_profit=0.3)
    # still holding
    assert out.sum() >= 1
