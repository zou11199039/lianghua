# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod


class StrategyBase(ABC):
    def __init__(self, strategy_name, config_params):
        self.strategy_name = strategy_name
        self.params = config_params

    @abstractmethod
    def on_init(self, context):
        """
        Called when strategy starts. Initialize indicators etc.
        """
        pass

    @abstractmethod
    def on_market_data(self, context, market_data):
        """
        Called when new market data arrives (daily or tick).
        market_data: Dictionary of DataFrames or current Tick object
        return: List of signal dicts
        """
        pass

    @abstractmethod
    def generate_signals(self, price_df):
        """Batch-style API for backtesting.

        Given a price DataFrame, return a Series of 0/1 signals
        aligned with price_df.index.
        """
        raise NotImplementedError

    def log(self, message):
        print(f"[{self.strategy_name}] {message}")
