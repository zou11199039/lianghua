# -*- coding: utf-8 -*-
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data.data_storage import DataStorage
from src.data.data_provider import DataProvider

def main():
    print("--- Verifying Data Engine ---")
    
    # 1. Init Storage
    storage = DataStorage()
    print("Storage initialized (DB + Parquet).")
    
    # 2. Init Provider
    provider = DataProvider(storage)
    print("Provider initialized.")
    
    stock_list = ['600000.SH', '000001.SZ']
    period = '1d'

    # 3. Test Download & Save
    print(f"Downloading data for {stock_list}...")
    try:
        provider.download_data(stock_list, period)
    except Exception as e:
        print(f"Download failed: {e}")
        # Continue to verify load even if download fails (might have cache)

    # 4. Test Load (Cache)
    print("Loading data from Cache (Parquet)...")
    data = provider.get_kline(stock_list, period, use_cache=True)
    
    for code, df in data.items():
        print(f"[{code}] loaded: {len(df)} rows.")
        if not df.empty:
            print(df.tail(3))
    
    # 5. Test DB Logging
    print("Testing DB Logging...")
    storage.log_trade({
        'code': '600000.SH',
        'action': 'BUY',
        'price': 10.5,
        'volume': 100,
        'strategy_name': 'TEST_VERIFY',
        'remark': 'Verification Run'
    })
    print("Trade logged.")

if __name__ == "__main__":
    main()
