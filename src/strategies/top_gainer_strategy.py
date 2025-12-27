# -*- coding: utf-8 -*-
from .strategy_base import StrategyBase
from .gemini_agent import GeminiAgent
import json


class TopGainerStrategy(StrategyBase):
    def __init__(self, strategy_name, config_params, gemini_agent: GeminiAgent):
        super().__init__(strategy_name, config_params)
        self.gemini = gemini_agent

    def on_init(self, context):
        self.log("Initializing Top Gainer Strategy...")

    def on_market_data(self, context, market_data):
        self.log("Analyzing market data...")
        signals = []

        # 1. Quantitative Filter (e.g., Momentum)
        candidates = []
        for code, df in market_data.items():
            if df.empty or len(df) < 5:
                continue

            # Simple Logic: 5-day return
            last_close = df["close"].iloc[-1]
            prev_close = df["close"].iloc[-5]
            pct_change = (last_close - prev_close) / prev_close

            if pct_change > 0.03:  # >3% in 5 days
                candidates.append(
                    {"code": code, "pct_change": pct_change, "price": last_close}
                )

        # Sort by return
        candidates.sort(key=lambda x: x["pct_change"], reverse=True)
        top_candidates = candidates[:5]

        # 2. LLM Filter (Optional)
        # In a real scenario, we would feed news about these stocks.
        # Here we mock a summary.
        if top_candidates and self.gemini.model:
            summary = f"Top momentum stocks: {[c['code'] for c in top_candidates]}"
            news_mock = (
                "Market sentiment is generally positive due to recent policy support."
            )

            self.log("Requesting Gemini analysis...")
            analysis_json = self.gemini.analyze_market(news_mock, summary)

            if analysis_json:
                self.log(f"Gemini Analysis: {analysis_json}")
                try:
                    analysis = json.loads(analysis_json)
                    # Filter based on LLM opinion.
                    # Simplified logic: take top 2 from quant list
                    # if sentiment is bullish.
                    if "Bullish" in analysis.get("sentiment", ""):
                        top_candidates = top_candidates[:3]
                except Exception as e:
                    self.log(f"Error parsing Gemini analysis: {e}")

        # 3. Generate Signals
        for item in top_candidates:
            signals.append(
                {
                    "code": item["code"],
                    "signal_type": "BUY",
                    "strength": 1.0,
                    "price": item["price"],
                    "volume": 100,
                    "source": self.strategy_name,
                }
            )

        return signals

    def generate_signals(self, price_df):
        """Simple batch API to satisfy StrategyBase.

        Return a Series of 0/1 based on 5-day momentum.
        """
        import pandas as pd

        if price_df is None or price_df.empty:
            return pd.Series(dtype="int")
        close = price_df["close"]
        pct = (close - close.shift(5)) / close.shift(5)
        signal = (pct > 0.03).astype(int)
        signal.index = close.index
        return signal
