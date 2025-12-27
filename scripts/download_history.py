# -*- coding: utf-8 -*-
"""
示例脚本：使用 DataProvider + QMTClient 下载历史行情并写入本地存储
用法示例：
  python scripts/download_history.py --codes 600000.SH,000001.SZ --start 2020-01-01 --period 1d

注意：需要先启动 QMT/迅投极速交易终端或提供快捷方式路径给 QMTClient
"""
import argparse
import os
import sys
import logging
from datetime import datetime
# Ensure project root is on sys.path so `from src...` imports work when running script directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.data.data_storage import DataStorage
from src.data.data_provider import DataProvider
from src.data.qmt_client import QMTClient

# Setup basic logging
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
logfile = os.path.join(LOG_DIR, f"download_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', handlers=[
    logging.FileHandler(logfile, encoding='utf-8'),
    logging.StreamHandler(sys.stdout)
])
logger = logging.getLogger('download_history')


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--codes", type=str, required=True, help="逗号分隔的股票代码列表，如 600000.SH,000001.SZ")
    p.add_argument("--period", type=str, default="1d")
    p.add_argument("--start", type=str, default="")
    p.add_argument("--end", type=str, default="")
    p.add_argument("--shortcut", type=str, default=None, help="桌面快捷方式路径（可选），用于自动启动交易终端")
    return p.parse_args()


def main():
    args = parse_args()
    codes = [c.strip() for c in args.codes.split(",") if c.strip()]

    # 初始化 Storage 和 Provider
    storage = DataStorage()
    provider = DataProvider(storage)
    qmt = QMTClient(shortcut_path=args.shortcut)

    logger.info("确保 QMT 交易终端已运行（若未运行会尝试启动）...")
    if not qmt.ensure_running():
        logger.warning("未检测到 QMT 终端运行，数据下载可能失败。请手动启动‘中航证券QMT实盘-交易端’并重试。")

    logger.info(f"开始下载 {len(codes)} 支股票的历史数据...")
    try:
        provider.download_data(codes, period=args.period, start_time=args.start, end_time=args.end)
        logger.info("下载完成。")
    except Exception as e:
        logger.exception("下载过程中出现异常：%s", e)
        raise


if __name__ == '__main__':
    main()
