import os
import time
import types
import pytest

from src.data import qmt_client


def test_ensure_started_uses_startfile_and_detects(tmp_path, monkeypatch):
    # create dummy shortcut file
    shortcut = tmp_path / "qmt.lnk"
    shortcut.write_text("dummy")

    state = {"running": False}

    def fake_is_qmt_running(process_name="xt_trader.exe"):
        return state["running"]

    def fake_startfile(path):
        # simulate that after starting, process becomes running
        assert path == str(shortcut)
        state["running"] = True

    monkeypatch.setattr(qmt_client, "is_qmt_running", fake_is_qmt_running)
    # os.startfile may not exist on non-windows; patch it
    monkeypatch.setattr(os, "startfile", fake_startfile, raising=False)

    assert qmt_client.ensure_qmt_started(str(shortcut), process_name="xt_trader.exe", timeout=2) is True


def test_download_history_retries_on_exception():
    class FakeXT:
        def __init__(self):
            self.calls = 0

        def download_history_data(self, code, **kwargs):
            self.calls += 1
            if self.calls < 2:
                raise RuntimeError("transient")
            return {"code": code, "ok": True}

    fake = FakeXT()
    client = qmt_client.QMTClient(xtdata_module=fake, retry=1, retry_delay=0)
    res = client.download_history("600000.SH")
    assert res == {"code": "600000.SH", "ok": True}
    assert fake.calls == 2


def test_get_market_data_and_snapshot_forward_calls():
    class FakeXT:
        def __init__(self):
            self.gmd_called = False
            self.snap_called = False

        def get_market_data_ex(self, **kwargs):
            self.gmd_called = True
            return {"600000.SH": "df"}

        def get_full_tick(self, stock_list):
            self.snap_called = True
            return ["tick1"]

    fake = FakeXT()
    client = qmt_client.QMTClient(xtdata_module=fake)

    md = client.get_market_data(["600000.SH"])
    assert md == {"600000.SH": "df"}
    assert fake.gmd_called

    snap = client.get_snapshot(["600000.SH"])
    assert snap == ["tick1"]
    assert fake.snap_called


def test_call_xtdata_raises_if_missing_attr():
    fake = types.SimpleNamespace()
    client = qmt_client.QMTClient(xtdata_module=fake)
    with pytest.raises(AttributeError):
        client.get_snapshot(["600000.SH"])  # get_full_tick missing


def test_start_and_context_manager(monkeypatch):
    called = {"count": 0}

    def fake_ensure(self, timeout=20):
        called["count"] += 1
        return True

    monkeypatch.setattr(qmt_client.QMTClient, "ensure_running", fake_ensure, raising=False)

    with qmt_client.QMTClient() as client:
        assert client is not None

    assert called["count"] == 1


def test_start_logs_when_not_started(monkeypatch, caplog):
    monkeypatch.setattr(qmt_client.QMTClient, "ensure_running", lambda self, timeout=1: False, raising=False)
    client = qmt_client.QMTClient()
    with caplog.at_level('WARNING'):
        ok = client.start(timeout=1)
    assert ok is False
    assert any("did not start" in r.message for r in caplog.records)
