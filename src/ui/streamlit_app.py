# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from src.strategies.momentum import ma_crossover_signal
from src.backtest.backtester import SimpleBacktester

st.title('量化交易系统 — 回测面板（MVP）')

codes = ['600000.SH']
code = st.selectbox('选择股票', codes)
period = st.selectbox('周期', ['1d'])
short = st.number_input('短期均线', value=5)
long = st.number_input('长期均线', value=20)

if st.button('运行回测'):
    feat_path = f'db/market_data/{code}_{period}.features.parquet'
    if not os.path.exists(feat_path):
        st.error('未找到特征文件，请先运行 scripts/test_preprocess.py')
    else:
        df = pd.read_parquet(feat_path)
        signal = ma_crossover_signal(df, short=int(short), long=int(long))
        bt = SimpleBacktester(initial_cash=100000)
        res = bt.run(df[['open','high','low','close']], signal)
        st.metric('累计收益', f"{res.total_return:.2%}")
        st.metric('年化收益', f"{res.annual_return:.2%}")
        st.metric('最大回撤', f"{res.max_drawdown:.2%}")
        st.metric('夏普', f"{res.sharpe:.2f}")
        st.line_chart(res.equity)
