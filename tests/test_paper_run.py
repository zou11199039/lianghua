# -*- coding: utf-8 -*-
import os
import json
from src.core.app import App


def test_run_paper_creates_report(tmp_path):
    cfg = 'config.example.json'
    assert os.path.exists(cfg)
    report_file = tmp_path / 'paper_report.json'

    app = App(config_path=cfg, mode='paper', dry_run=True)
    app.build_strategy()

    # ensure small stock pool for determinism
    app.config['strategy']['stocks_pool'] = ['600000.SH']

    from scripts.paper_run import run_paper
    reports = run_paper(config_path=cfg, rounds=1, stocks=['600000.SH'], report_path=str(report_file))

    assert isinstance(reports, list)
    assert len(reports) == 1
    assert report_file.exists()
    content = json.loads(report_file.read_text(encoding='utf-8'))
    assert isinstance(content, list)
