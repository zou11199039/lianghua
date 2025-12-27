# -*- coding: utf-8 -*-
from src.core.app import App


def test_app_starts_receipt_listener(monkeypatch):
    app = App(config_path='config.example.json', mode='live', dry_run=False)

    called = {'start': False}
    def fake_start():
        called['start'] = True
        return True
    def fake_start_listener(poll_interval=1.0):
        called['listener'] = True
    def fake_stop_listener():
        called['stopped'] = True

    # replace methods on the existing trader instance
    monkeypatch.setattr(app.trader, 'start', fake_start)
    monkeypatch.setattr(app.trader, 'start_receipt_listener', fake_start_listener)
    monkeypatch.setattr(app.trader, 'stop_receipt_listener', fake_stop_listener)

    res = app.start_trader_if_needed()
    assert res is True
    assert called.get('listener') is True

    # shutdown should call stop_receipt_listener
    app.shutdown()
    assert called.get('stopped') is True
