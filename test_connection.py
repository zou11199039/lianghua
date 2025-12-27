# -*- coding: utf-8 -*-
from xtquant import xtdata
from xtquant import xttrader

print("Testing QMT Environment...")

# Test Data
print("\n1. Testing XtData...")
try:
    code = "600000.SH"
    xtdata.download_history_data(code, period="1d")
    data = xtdata.get_market_data_ex([], [code], period="1d", count=5)
    print(f"Data retrieved for {code}:")
    print(data[code])
except Exception as e:
    print(f"XtData Error: {e}")

# Test Trader connection (Mock check)
print("\n2. Checking XtTrader Library...")
try:
    print(f"XtTrader version: {xttrader.__file__}")
    print("XtTrader import successful.")
except Exception as e:
    print(f"XtTrader Import Error: {e}")
