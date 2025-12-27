# -*- coding: utf-8 -*-
import pandas as pd
import os, sys
# ensure project root is on sys.path when running from scripts/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.data.data_storage import DataStorage
import sqlite3

print('Start test insert')
ds = DataStorage()
idx = pd.to_datetime(['2030-01-02'])
df = pd.DataFrame({'open':[1.0],'high':[1.0],'low':[1.0],'close':[1.0],'volume':[100]}, index=idx)
inserted = ds.save_market_data(df, '600000.SH', '1d')
print('inserted', inserted)
# log a signal
if inserted > 0:
    ds.log_signal({'code':'600000.SH','signal_type':'test_insert','strength':float(inserted),'source':'unit_test'})

conn = sqlite3.connect('db/quant.db')
print('signals:')
print(pd.read_sql('select * from signals order by id desc limit 5', conn))
print('trade_logs:')
print(pd.read_sql('select * from trade_logs order by id desc limit 5', conn))
conn.close()
