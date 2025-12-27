# -*- coding: utf-8 -*-
"""
数据质量验证与预处理模块
功能：
- 缺失值处理（填充/删除）
- OHLC 对齐/类型转换/索引标准化
- 复权占位（简单 placeholder，若需要可以和 qmt 的复权数据结合）
- 因子计算（移动平均、动量等）
"""
from typing import List, Optional
import pandas as pd
import numpy as np


def ensure_datetime_index(
    df: pd.DataFrame, time_col: Optional[str] = None
) -> pd.DataFrame:
    """确保 DataFrame 使用 DatetimeIndex。尝试多种常见列名/格式。"""
    df = df.copy()
    if isinstance(df.index, pd.DatetimeIndex):
        return df

    if time_col and time_col in df.columns:
        try:
            df.index = pd.to_datetime(df[time_col])
            return df
        except Exception:
            pass

    # 尝试常见的 'time' (ms since epoch) 或整数型 YYYYMMDD
    if "time" in df.columns:
        try:
            df.index = pd.to_datetime(df["time"], unit="ms")
            return df
        except Exception:
            pass

    # 尝试把现有索引解析为日期
    try:
        df.index = pd.to_datetime(df.index)
        return df
    except Exception:
        pass

    # 最后尝试解析 'date' 列
    if "date" in df.columns:
        df.index = pd.to_datetime(df["date"])
        return df

    raise ValueError("无法解析时间索引，请提供 time_col 或确保有 date/time 列")


def fill_missing(df: pd.DataFrame, method: str = "ffill") -> pd.DataFrame:
    """填充缺失值，默认向前填充，再用 0 填充剩余 NaN。"""
    df = df.copy()
    if method == "ffill":
        df = df.fillna(method="ffill")
    elif method == "bfill":
        df = df.fillna(method="bfill")
    elif method == "interpolate":
        df = df.interpolate()
    else:
        df = df.fillna(method)

    df = df.fillna(0)
    return df


def calculate_moving_averages(
    df: pd.DataFrame, windows: List[int] = [5, 20, 60]
) -> pd.DataFrame:
    """计算并返回带有 MA 特征的 DataFrame（在列名前加上 ma_{w}）。"""
    df = df.copy()
    for w in windows:
        df[f"ma_{w}"] = df["close"].rolling(window=w, min_periods=1).mean()
    return df


def calculate_momentum(df: pd.DataFrame, period: int = 10) -> pd.DataFrame:
    df = df.copy()
    df[f"mom_{period}"] = df["close"] / df["close"].shift(period) - 1
    return df


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    df = df.copy()
    delta = df["close"].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.rolling(period, min_periods=1).mean()
    ma_down = down.rolling(period, min_periods=1).mean()
    rs = ma_up / (ma_down.replace(0, np.nan))
    df[f"rsi_{period}"] = 100 - (100 / (1 + rs))
    df[f"rsi_{period}"] = df[f"rsi_{period}"].fillna(50)
    return df


def generate_features(df: pd.DataFrame) -> pd.DataFrame:
    """统一入口：标准化 index、填充、并计算常见因子。"""
    df = ensure_datetime_index(df)
    df = df.sort_index()
    df = fill_missing(df, method="ffill")
    df = calculate_moving_averages(df, windows=[5, 10, 20])
    df = calculate_momentum(df, period=10)
    df = calculate_rsi(df, period=14)
    return df
