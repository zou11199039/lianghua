# -*- coding: utf-8 -*-
"""
轻量 QMT 客户端封装：检查终端运行、下载历史数据、获取快照。

改进点：
- 更稳健的启动逻辑（使用 os.startfile 在 Windows 上打开快捷方式）
- 为 xtdata 调用提供依赖注入（便于测试）
- 增加可配置重试/延迟与异常封装
"""
import subprocess
import os
import time
import logging
from typing import List, Dict, Any, Optional

try:
    from xtquant import xtdata as _default_xtdata
except Exception as e:  # pragma: no cover - environment dependent
    _default_xtdata = None
    logger = logging.getLogger(__name__)
    logger.debug("xtquant.xtdata not available: %s", e)
logger = logging.getLogger(__name__)


def is_qmt_running(process_name: str = "xt_trader.exe") -> bool:
    """判断 QMT 交易终端进程是否在运行（Windows）。

    使用 `tasklist` 并做容错处理，返回布尔值。
    """
    try:
        out = subprocess.check_output("tasklist", shell=True, text=True)
        return process_name.lower() in out.lower()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.debug("is_qmt_running: tasklist failed: %s", e)
        return False
    except Exception as e:
        logger.exception("Unexpected error checking qmt process: %s", e)
        return False


def ensure_qmt_started(shortcut_path: Optional[str] = None, process_name: str = "xt_trader.exe", timeout: int = 20) -> bool:
    """如果 QMT 未运行，尝试通过快捷方式启动（如果提供），并等待直到可用或超时。

    在 Windows 上优先使用 `os.startfile` 打开快捷方式（适用于 .lnk 等）。
    返回 True 表示终端正在运行或已成功启动。
    """
    if is_qmt_running(process_name):
        return True

    if shortcut_path and os.path.exists(shortcut_path):
        try:
            # 在 Windows 上更可靠的方式是 os.startfile
            if os.name == 'nt':
                os.startfile(shortcut_path)
            else:
                subprocess.Popen([shortcut_path], shell=False)
        except Exception as e:
            logger.warning("Failed to start QMT via shortcut %s: %s", shortcut_path, e)

    start = time.time()
    while time.time() - start < timeout:
        if is_qmt_running(process_name):
            return True
        time.sleep(1)

    return False


class QMTClient:
    """QMT 客户端封装。

    参数:
      - shortcut_path: 系统上的快捷方式路径（用于通过代码启动 QMT）
      - process_name: QMT 可执行程序名（用于检测进程）
      - xtdata_module: 可注入的 xtdata 模块（便于测试）
      - retry: 默认重试次数
      - retry_delay: 重试间隔（秒）
    """

    def __init__(
        self,
        shortcut_path: Optional[str] = None,
        process_name: str = "xt_trader.exe",
        xtdata_module: Any = _default_xtdata,
        retry: int = 1,
        retry_delay: float = 1.0,
    ) -> None:
        self.shortcut_path = shortcut_path
        self.process_name = process_name
        self._xtdata = xtdata_module
        if self._xtdata is None:
            logger.warning("xtquant.xtdata not available; inject an xtdata_module to use data methods in tests or in environments without xtquant installed.")
        self._retry = max(0, int(retry))
        self._retry_delay = float(retry_delay)

    def ensure_running(self, timeout: int = 20) -> bool:
        return ensure_qmt_started(self.shortcut_path, self.process_name, timeout)

    def _call_xtdata(self, func_name: str, *args, **kwargs):
        """通过注入的 xtdata 模块调用函数，支持简单的重试与日志。"""
        func = getattr(self._xtdata, func_name, None)
        if not callable(func):
            raise AttributeError(f"xtdata has no attribute '{func_name}'")

        last_exc = None
        attempts = max(1, self._retry + 1)
        for i in range(attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exc = e
                logger.warning("xtdata.%s failed (attempt %d/%d): %s", func_name, i + 1, attempts, e)
                if i + 1 < attempts:
                    time.sleep(self._retry_delay)
        # raise the last exception for caller to handle
        raise last_exc

    def download_history(self, code: str, period: str = "1d", start_time: str = "", end_time: str = ""):
        """调用 xtdata.download_history_data。"""
        return self._call_xtdata("download_history_data", code, period=period, start_time=start_time, end_time=end_time)

    def get_market_data(self, stock_list: List[str], period: str = "1d", start_time: str = "", end_time: str = "") -> Dict[str, Any]:
        return self._call_xtdata(
            "get_market_data_ex",
            field_list=[],
            stock_list=stock_list,
            period=period,
            start_time=start_time,
            end_time=end_time,
            count=-1,
        )

    def get_snapshot(self, stock_list: List[str]):
        return self._call_xtdata("get_full_tick", stock_list)

    def start(self, timeout: int = 20) -> bool:
        """尝试启动/等待 QMT 运行；返回是否成功。"""
        started = self.ensure_running(timeout)
        if started:
            logger.info("QMT is running (process=%s)", self.process_name)
        else:
            logger.warning("QMT did not start within %ss (process=%s)", timeout, self.process_name)
        return started

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        # 不吞掉异常，按常规语义向外抛出
        return False
