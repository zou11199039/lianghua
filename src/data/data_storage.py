# -*- coding: utf-8 -*-
import os
import sqlite3
import pandas as pd
from datetime import datetime


class DataStorage:
    def __init__(self, db_path="db/quant.db", data_path="db/market_data"):
        self.db_path = db_path
        self.data_path = data_path
        self._init_db()
        self._init_fs()

    def _init_fs(self):
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)

    def _init_db(self):
        """Initialize SQLite database with necessary tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Table: Trade Logs
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS trade_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            code TEXT,
            action TEXT,
            price REAL,
            volume INTEGER,
            strategy_name TEXT,
            remark TEXT
        )
        """
        )

        # Table: Signals
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            code TEXT,
            signal_type TEXT,
            strength REAL,
            source TEXT
        )
        """
        )

        conn.commit()
        conn.close()

    def save_market_data(self, df, stock_code, period="1d"):
        """
        Save market data to Parquet file with simple incremental (merge/upsert) logic.
        Returns the number of newly inserted rows.
        """
        if df is None or df.empty:
            return 0

        filename = f"{stock_code}_{period}.parquet"
        file_path = os.path.join(self.data_path, filename)

        # Normalize index: if DataFrame has a column named 'date' or 'time'
        # that is more reliable, prefer using it as index for dedup/merge.
        # Otherwise use existing index.
        new_df = df.copy()
        try:
            # If 'date' column exists, set as index
            if "date" in new_df.columns:
                new_df.index = pd.to_datetime(new_df["date"])
            elif "time" in new_df.columns:
                # if 'time' is epoch in milliseconds
                try:
                    new_df.index = pd.to_datetime(new_df["time"], unit="ms")
                except Exception:
                    # fallback: try interpret as YYYYMMDD-like int index
                    pass
        except Exception:
            pass

        # If index is not unique, drop duplicates keeping last
        if not new_df.index.is_unique:
            new_df = new_df[~new_df.index.duplicated(keep="last")]

        # Read existing data if available and merge
        if os.path.exists(file_path):
            try:
                existing = pd.read_parquet(file_path)

                # Normalize indexes to DatetimeIndex where possible
                # to avoid mixed-type comparison
                def try_normalize_index(df):
                    idx = df.index
                    # Try parse from epoch ms
                    try:
                        new_idx = (
                            pd.to_datetime(df["time"], unit="ms")
                            if "time" in df.columns
                            else None
                        )
                        if new_idx is not None and not new_idx.isna().all():
                            df = df.copy()
                            df.index = new_idx
                            return df
                    except Exception:
                        pass

                    # Try parse index as int YYYYMMDD
                    try:
                        idx_str = idx.astype(str)
                        new_idx = pd.to_datetime(
                            idx_str, format="%Y%m%d", errors="coerce"
                        )
                        if not new_idx.isna().all():
                            df = df.copy()
                            df.index = new_idx
                            return df
                    except Exception:
                        pass

                    # Try generic to_datetime
                    try:
                        new_idx = pd.to_datetime(idx, errors="coerce")
                        if not new_idx.isna().all():
                            df = df.copy()
                            df.index = new_idx
                            return df
                    except Exception:
                        pass

                    return df

                existing = try_normalize_index(existing)
                new_df = try_normalize_index(new_df)

                # If still different types, coerce both to string
                # to avoid type comparison issues
                if existing.index.dtype != new_df.index.dtype:
                    existing.index = existing.index.astype(str)
                    new_df.index = new_df.index.astype(str)

                merged = pd.concat([existing, new_df])
                merged = merged[~merged.index.duplicated(keep="last")]
                try:
                    merged.sort_index(inplace=True)
                except Exception:
                    # If sort fails due to incomparable types, keep as-is
                    pass
                inserted = max(0, len(merged) - len(existing))
            except Exception as e:
                print(
                    f"Warning: could not merge with existing parquet ({e}), overwriting"
                )
                merged = new_df.sort_index()
                inserted = len(merged)
        else:
            merged = new_df.sort_index()
            inserted = len(merged)

        # Write back
        merged.to_parquet(file_path, engine="pyarrow")
        print(
            f"Saved {len(merged)} records (+{inserted} new) "
            f"for {stock_code} to {file_path}"
        )
        return int(inserted)

    def load_market_data(self, stock_code, period="1d"):
        """Load market data from Parquet."""
        filename = f"{stock_code}_{period}.parquet"
        file_path = os.path.join(self.data_path, filename)

        if os.path.exists(file_path):
            return pd.read_parquet(file_path)
        return None

    def log_trade(self, trade_dict):
        """Log a trade execution to SQLite."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
        INSERT INTO trade_logs (
            timestamp,
            code,
            action,
            price,
            volume,
            strategy_name,
            remark
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                trade_dict.get("code"),
                trade_dict.get("action"),
                trade_dict.get("price"),
                trade_dict.get("volume"),
                trade_dict.get("strategy_name", "manual"),
                trade_dict.get("remark", ""),
            ),
        )

        conn.commit()
        conn.close()

    def log_signal(self, signal_dict):
        """Log a strategy signal to SQLite."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
        INSERT INTO signals (timestamp, code, signal_type, strength, source)
        VALUES (?, ?, ?, ?, ?)
        """,
            (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                signal_dict.get("code"),
                signal_dict.get("signal_type"),
                signal_dict.get("strength", 0.0),
                signal_dict.get("source", "unknown"),
            ),
        )

        conn.commit()
        conn.close()
