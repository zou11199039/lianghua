import os
from src.core.app import App


def test_app_initializes():
    cfg = 'config.example.json'
    assert os.path.exists(cfg)
    app = App(config_path=cfg, mode='paper', dry_run=True)
    assert app.storage is not None
    assert app.data_provider is not None
    assert app.notifier is not None
    assert app.trader is not None
    # Strategy may be lazy; build it explicitly
    strat = app.build_strategy()
    assert strat is not None
