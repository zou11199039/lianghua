# -*- coding: utf-8 -*-
"""
Simple scheduler for periodic incremental data sync using APScheduler.
- Loads configuration from config.json or environment
- Schedules download jobs for a configurable stock list and period
- Writes logs to logs/scheduler_YYYYMMDD_HHMMSS.log

Usage (development):
  python scripts/scheduler.py --interval 60  # run job every 60 seconds (for testing)

In production, run as a background process (Windows: NSSM/Task Scheduler / Services; Linux: systemd)
"""
import os
import sys
import json
import logging
from datetime import datetime
from argparse import ArgumentParser

# Ensure project root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.data.data_storage import DataStorage
from src.data.data_provider import DataProvider
from src.data.qmt_client import QMTClient

# Optional: APScheduler
try:
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.executors.pool import ThreadPoolExecutor
except Exception:
    BlockingScheduler = None

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
logfile = os.path.join(
    LOG_DIR, f"scheduler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(logfile, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("scheduler")


def load_config(cfg_path="config.json"):
    cfg = {}
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    else:
        logger.warning("config.json not found, using defaults")
    return cfg


def job_sync(codes, period, qmt_shortcut=None):
    try:
        storage = DataStorage()
        provider = DataProvider(storage)
        qmt = QMTClient(shortcut_path=qmt_shortcut)

        logger.info("Job started: codes=%s period=%s", codes, period)
        if not qmt.ensure_running():
            logger.warning(
                "QMT terminal not running, job will attempt to proceed (may fail)"
            )

        provider.download_data(codes, period=period)
        logger.info("Job finished")
    except Exception as e:
        logger.exception("Job failed: %s", e)


def main():
    p = ArgumentParser()
    p.add_argument(
        "--interval", type=int, default=60, help="Interval in seconds for testing"
    )
    p.add_argument(
        "--codes", type=str, default="", help="Comma-separated codes to override config"
    )
    p.add_argument("--period", type=str, default="1d")
    p.add_argument("--shortcut", type=str, default=None)
    args = p.parse_args()

    cfg = load_config("config.json")
    # Default watch list, can be overridden by config or CLI
    codes = [
        c.strip()
        for c in (args.codes or cfg.get("watch_list", "600000.SH")).split(",")
        if c.strip()
    ]
    period = args.period or cfg.get("period", "1d")
    shortcut = args.shortcut or cfg.get("qmt", {}).get("shortcut_path")

    if BlockingScheduler is None:
        logger.error(
            "APScheduler not installed. Install with `pip install apscheduler`"
        )
        return

    executors = {"default": ThreadPoolExecutor(4)}
    sched = BlockingScheduler(executors=executors)

    # For production we would schedule by cron or interval; here schedule by interval seconds (for testing)
    sched.add_job(
        lambda: job_sync(codes, period, qmt_shortcut=shortcut),
        "interval",
        seconds=args.interval,
        id="data_sync",
    )

    logger.info("Scheduler started (interval=%ds) codes=%s", args.interval, codes)
    try:
        sched.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopping")


if __name__ == "__main__":
    main()
