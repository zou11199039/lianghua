# -*- coding: utf-8 -*-
import pandas as pd
from xtquant import xtdata


class DataLoader:
    def __init__(self):
        print("Initializing DataLoader...")

    def download_data(
        self, stock_list, period="1d", start_time="", end_time="", count=-1
    ):
        """
        Download historical data to local cache.
        """
        print(f"Downloading data for {len(stock_list)} stocks...")
        for stock_code in stock_list:
            xtdata.download_history_data(
                stock_code, period=period, start_time=start_time, end_time=end_time
            )
        print("Download complete.")

    def get_kline(self, stock_list, period="1d", start_time="", end_time="", count=-1):
        """
        Get K-line data as a Dictionary of DataFrames.
        """
        data = xtdata.get_market_data_ex(
            field_list=[],  # empty list means all fields
            stock_list=stock_list,
            period=period,
            start_time=start_time,
            end_time=end_time,
            count=count,
            dividend_type="none",
            fill_data=True,
        )
        return data

    def get_snapshot(self, stock_list):
        """
        Get real-time full tick data.
        """
        return xtdata.get_full_tick(stock_list)

    def get_sector_list(self, sector_name="沪深A股"):
        """
        Get stock list for a specific sector.
        """
        return xtdata.get_stock_list_in_sector(sector_name)
