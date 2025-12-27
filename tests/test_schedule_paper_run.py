# -*- coding: utf-8 -*-
from src.core.app import App


def test_schedule_paper_run_registers_job():
    app = App(config_path="config.example.json", mode="paper", dry_run=True)
    res = app.schedule_paper_run(
        minutes=1, rounds=1, stocks=["600000.SH"], report_path="reports/test_sched.json"
    )
    assert res is True
