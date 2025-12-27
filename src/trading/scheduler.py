# -*- coding: utf-8 -*-
import time
import threading
import warnings

try:
    import schedule

    _HAS_SCHEDULE = True
except Exception:
    schedule = None
    _HAS_SCHEDULE = False


class Scheduler:
    def __init__(self):
        self.running = False
        self.thread = None
        self._tasks = []
        if not _HAS_SCHEDULE:
            warnings.warn(
                "Optional dependency 'schedule' not found. Scheduler will accept jobs but will only run a simple loop."
            )

    def add_daily_job(self, time_str, job_func, *args):
        """Register a job to run daily at the given HH:MM. If 'schedule' library is available it will be used; otherwise the job is stored and will run approximately when time matches."""
        if _HAS_SCHEDULE:
            schedule.every().day.at(time_str).do(job_func, *args)
        else:
            self._tasks.append(("daily", time_str, job_func, args))

    def add_interval_job(self, minutes, job_func, *args):
        """Register a job to run every N minutes."""
        if _HAS_SCHEDULE:
            schedule.every(minutes).minutes.do(job_func, *args)
        else:
            self._tasks.append(("interval", minutes, job_func, args))

    def _run_loop(self):
        while self.running:
            if _HAS_SCHEDULE:
                schedule.run_pending()
            else:
                # Very simple fallback: run interval tasks approximately
                now = time.strftime("%H:%M")
                for kind, spec, func, args in list(self._tasks):
                    try:
                        if kind == "daily":
                            if now == spec:
                                func(*args)
                        elif kind == "interval":
                            func(*args)
                    except Exception:
                        pass
                time.sleep(60)

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            print("Scheduler started.")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
            print("Scheduler stopped.")
