# -*- coding: utf-8 -*-
import pandas as pd
from scripts.paper_run import run_paper
from src.core.app import App


class DummyProvider:
    def __init__(self, df_map):
        self._df = df_map

    def download_data(self, stocks):
        pass

    def get_kline(self, stocks):
        return self._df


class DummyStrategy:
    def __init__(self):
        self.strategy_name = "Dummy"

    def on_market_data(self, ctx, market_data):
        # produce one buy signal for 600000
        return [
            {
                "code": "600000.SH",
                "signal_type": "BUY",
                "volume": 10,
                "price": market_data["600000.SH"]["close"].iloc[-1],
            }
        ]


def test_paper_pnl_estimation(tmp_path):
    # build a fake app
    app = App(config_path="config.example.json", mode="paper", dry_run=True)
    # create kline with upward move
    dates = pd.date_range("2020-01-01", periods=3, freq="D")
    closes = [10.0, 11.0, 12.0]
    df = pd.DataFrame({"close": closes}, index=dates)

    app.data_provider = DummyProvider({"600000.SH": df})
    app.strategy = DummyStrategy()

    reports = run_paper(
        app=app, rounds=1, stocks=["600000.SH"], report_path=str(tmp_path / "r.json")
    )
    assert reports is not None
    assert len(reports) == 1
    assert reports[0]["executed"] == 1
    # simulated pnl should be >0 since trend is up and buy signal
    assert reports[0]["simulated_pnl"] > 0
