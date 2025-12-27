# -*- coding: utf-8 -*-
"""
控制台版本调试脚本 - 不依赖GUI
用于快速测试核心功能：数据、策略、交易模块
"""
import sys
import json

# 导入核心模块
from src.data.data_storage import DataStorage
from src.data.data_provider import DataProvider
from src.strategies.gemini_agent import GeminiAgent
from src.strategies.top_gainer_strategy import TopGainerStrategy

def load_config():
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def test_data_module():
    print("\n=== 测试数据模块 ===")
    try:
        storage = DataStorage()
        provider = DataProvider(storage)
        
        # 测试下载和读取
        stock_list = ['600000.SH']
        print(f"下载 {stock_list} 的数据...")
        provider.download_data(stock_list, period='1d')
        
        # 读取数据
        data = provider.get_kline(stock_list, use_cache=True)
        if data:
            for code, df in data.items():
                print(f"[OK] {code}: {len(df)} records")
                print(df.tail(3))
        return True
    except Exception as e:
        print(f"[ERR] Data Module Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_strategy_module():
    print("\n=== Testing Strategy Module ===")
    try:
        config = load_config()
        
        # Create Gemini Agent
        gemini = GeminiAgent(api_key=config['api_keys'].get('gemini_api_key'))
        
        # Create Strategy
        strategy = TopGainerStrategy(
            "Test Strategy",
            config['strategy'],
            gemini
        )
        
        # Mock Data
        from src.data.data_storage import DataStorage
        from src.data.data_provider import DataProvider
        
        storage = DataStorage()
        provider = DataProvider(storage)
        stock_list = config['strategy']['stocks_pool'][:2]
        
        print(f"Fetching data for {stock_list}...")
        market_data = provider.get_kline(stock_list, use_cache=True)
        
        # Run Strategy
        print("Running analysis...")
        signals = strategy.on_market_data(None, market_data)
        
        print(f"[OK] Signals Generated: {len(signals)}")
        for sig in signals:
            print(f"  - {sig}")
        
        return True
    except Exception as e:
        print(f"[ERR] Strategy Module Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_trade_module():
    print("\n=== Testing Trade Module ===")
    print("Note: Trade module requires MiniQMT running.")
    try:
        from src.trading.trade_executor import TradeExecutor
        config = load_config()
        
        executor = TradeExecutor(
            account_id=config['account']['qmt_account_id'],
            mini_qmt_path=config['account']['mini_qmt_path']
        )
        print("[OK] TradeExecutor Initialized")
        return True
    except Exception as e:
        print(f"[ERR] Trade Module Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 50)
    print("QMT Quant System - Console Debug")
    print("=" * 50)
    
    results = {}
    
    # Test Modules
    results['Data'] = test_data_module()
    results['Strategy'] = test_strategy_module()
    results['Trade'] = test_trade_module()
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    for name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {name}: {status}")
    print("=" * 50)

if __name__ == "__main__":
    main()
