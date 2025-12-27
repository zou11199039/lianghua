# -*- coding: utf-8 -*-
import pandas as pd


class SimpleMAStrategy:
    def __init__(self, short_window=5, long_window=20):
        self.short_window = short_window
        self.long_window = long_window

    def run(self, stock_data_dict):
        """
        Run the strategy on the provided data.
        Returns a list of buy/sell signals.
        """
        signals = []

        for stock_code, df in stock_data_dict.items():
            if df is None or df.empty or len(df) < self.long_window:
                continue

            # Calculate Moving Averages
            # Note: XtData 'close' column might be named differently depending on request,
            # but usually it's just 'close' in the standard dataframe
            if "close" not in df.columns:
                print(f"Checking columns for {stock_code}: {df.columns}")
                # Fallback if necessary
                continue

            df["short_mavg"] = (
                df["close"].rolling(window=self.short_window, min_periods=1).mean()
            )
            df["long_mavg"] = (
                df["close"].rolling(window=self.long_window, min_periods=1).mean()
            )

            # Simple logic:
            # If short > long and previous short <= previous long -> BUY
            # If short < long and previous short >= previous long -> SELL

            curr_short = df["short_mavg"].iloc[-1]
            curr_long = df["long_mavg"].iloc[-1]
            prev_short = df["short_mavg"].iloc[-2]
            prev_long = df["long_mavg"].iloc[-2]

            price = df["close"].iloc[-1]

            if curr_short > curr_long and prev_short <= prev_long:
                signals.append(
                    {
                        "code": stock_code,
                        "action": "buy",
                        "price": price,
                        "volume": 100,  # Fixed volume for demo
                    }
                )
            elif curr_short < curr_long and prev_short >= prev_long:
                signals.append(
                    {
                        "code": stock_code,
                        "action": "sell",
                        "price": price,
                        "volume": 100,
                    }
                )

        return signals
