# -*- coding: utf-8 -*-
from xtquant import xtdata
from .data_storage import DataStorage
import pandas as pd
import logging

logger = logging.getLogger('data_provider')

class DataProvider:
    def __init__(self, storage: DataStorage):
        self.storage = storage

    def download_data(self, stock_list, period='1d', start_time='', end_time=''):
        """
        Download data from QMT and save to Parquet.
        """
        logger.info(f"Downloading data for {len(stock_list)} stocks...")
        for code in stock_list:
            # 1. Trigger download in QMT client
            try:
                xtdata.download_history_data(code, period=period, start_time=start_time, end_time=end_time)
            except Exception as e:
                logger.exception("Error downloading history for %s: %s", code, e)
                continue

            # 2. Read from QMT local cache
            # Note: xtdata.get_market_data_ex returns a dict {code: dataframe}
            try:
                data_dict = xtdata.get_market_data_ex(
                    field_list=[], 
                    stock_list=[code], 
                    period=period, 
                    start_time=start_time, 
                    end_time=end_time,
                    count=-1
                )
            except Exception as e:
                logger.exception("get_market_data_ex failed for %s: %s", code, e)
                continue

            if not data_dict:
                logger.warning("xtdata.get_market_data_ex returned no data for %s", code)
                continue

            if code in data_dict and not data_dict[code].empty:
                # 3. Save to our own storage (Parquet)
                try:
                    inserted = self.storage.save_market_data(data_dict[code], code, period)
                    # Log a download signal when new rows were inserted
                    if inserted and inserted > 0:
                        self.storage.log_signal({
                            'code': code,
                            'signal_type': 'download',
                            'strength': float(inserted),
                            'source': 'qmt_download'
                        })
                        logger.info("%s: inserted %d new rows", code, inserted)
                    else:
                        logger.info("%s: no new rows", code)
                except Exception as e:
                    logger.exception("Error saving data for %s: %s", code, e)
            else:
                logger.warning("No data found for %s", code)
        
        logger.info("Download and Storage Sync complete.")

    def get_kline(self, stock_list, period='1d', use_cache=True):
        """
        Get K-line data. 
        If use_cache is True, try to load from Parquet first.
        If missing or empty, fetch from QMT.
        """
        result = {}
        missing_stocks = []

        if use_cache:
            for code in stock_list:
                df = self.storage.load_market_data(code, period)
                if df is not None and not df.empty:
                    result[code] = df
                else:
                    missing_stocks.append(code)
        else:
            missing_stocks = stock_list

        if missing_stocks:
            print(f"Fetching {len(missing_stocks)} stocks from QMT...")
            data_dict = xtdata.get_market_data_ex(
                field_list=[], 
                stock_list=missing_stocks, 
                period=period, 
                count=-1
            )
            result.update(data_dict)

        return result

    def get_snapshot(self, stock_list):
        """
        Get real-time snapshot (Level 1 Tick).
        """
        return xtdata.get_full_tick(stock_list)
