# -*- coding: utf-8 -*-
"""Paper-run script: run configured strategy in paper mode for a few iterations,
log simulated trades and produce a simple report.

Usage:
    python scripts/paper_run.py --config config.json --rounds 1 --report reports/paper_run.json
"""
import argparse
import json
import os
import time
from datetime import datetime

from src.core.app import App


def run_paper(
    config_path="config.json",
    rounds=1,
    stocks=None,
    report_path=None,
    app=None,
    report_format="json",
):
    """Run paper-mode simulation. Accept optional `app` to make testing deterministic."""
    app = app or App(config_path=config_path, mode="paper", dry_run=True)
    app.build_strategy()

    # Ensure log dir
    reports = []

    stock_pool = stocks or app.config.get("strategy", {}).get("stocks_pool", [])
    if not stock_pool:
        app.logger.warning("No stocks configured for paper run; exiting")
        return None

    for r in range(rounds):
        app.logger.info(f"Paper run iteration {r+1}/{rounds} started")

        # 1) download/update data
        try:
            app.data_provider.download_data(stock_pool)
        except Exception:
            app.logger.debug(
                "Data provider download skipped in paper run (may be mocked in tests)"
            )

        kline_data = app.data_provider.get_kline(stock_pool)

        # 2) get signals
        signals = app.strategy.on_market_data(None, kline_data)
        executed = 0
        simulated_pnl = 0.0
        details = []

        for sig in signals:
            sig["source"] = app.strategy.strategy_name
            # submit via OrderManager (paper_mode enforced by app)
            oid = app.order_manager.submit_signal(sig)
            if oid and str(oid).startswith("PAPER-"):
                executed += 1
                # log trade
                trade = {
                    "code": sig.get("code"),
                    "action": sig.get("signal_type"),
                    "price": sig.get("price"),
                    "volume": sig.get("volume"),
                    "strategy_name": app.strategy.strategy_name,
                    "remark": "paper_run",
                }
                try:
                    app.storage.log_trade(trade)
                except Exception as e:
                    app.logger.exception("Failed to log trade: %s", e)

                # estimate pnl using last two bars momentum as proxy for next bar
                df = kline_data.get(sig.get("code"))
                pnl = 0.0
                if df is not None and len(df) >= 2:
                    # use last two closes to estimate immediate next move
                    last = float(df["close"].iloc[-1])
                    prev = float(df["close"].iloc[-2])
                    est_move = last - prev
                    # buy -> profit = est_move * volume; sell -> inverse
                    if sig.get("signal_type", "").upper() == "BUY":
                        pnl = est_move * float(sig.get("volume", 0))
                    else:
                        pnl = -est_move * float(sig.get("volume", 0))

                simulated_pnl += pnl

                details.append({"signal": sig, "order_id": oid, "pnl": pnl})

        report = {
            "timestamp": datetime.now().isoformat(),
            "iteration": r + 1,
            "signals": len(signals),
            "executed": executed,
            "simulated_pnl": simulated_pnl,
            "details_count": len(details),
        }
        reports.append(report)
        app.logger.info(
            f"Paper run iter {r+1}: signals={len(signals)} executed={executed} pnl={simulated_pnl}"
        )

        # small delay between rounds
        time.sleep(0.5)

    if report_path:
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        fmt = report_format.lower() if "report_format" in locals() else "json"
        if fmt == "jsonl":
            with open(report_path, "w", encoding="utf-8") as f:
                for rec in reports:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        elif fmt == "csv":
            # flatten basic fields to CSV
            import csv

            keys = [
                "timestamp",
                "iteration",
                "signals",
                "executed",
                "simulated_pnl",
                "details_count",
            ]
            csv_path = (
                report_path if report_path.endswith(".csv") else report_path + ".csv"
            )
            with open(csv_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                for rec in reports:
                    writer.writerow({k: rec.get(k) for k in keys})
        else:
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(reports, f, indent=2, ensure_ascii=False)

    return reports


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--rounds", type=int, default=1)
    parser.add_argument("--stocks", nargs="*")
    parser.add_argument("--report", default="reports/paper_run.json")
    args = parser.parse_args()

    res = run_paper(
        config_path=args.config,
        rounds=args.rounds,
        stocks=args.stocks,
        report_path=args.report,
    )
    print("Paper run result:", res)
