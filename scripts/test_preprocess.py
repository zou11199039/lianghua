# -*- coding: utf-8 -*-
"""测试预处理模块：读取已下载的 parquet，运行生成特征并保存到 new parquet（用于回测）"""
import os
import pandas as pd
from src.data.preprocessor import generate_features

p = "db/market_data/600000.SH_1d.parquet"
if not os.path.exists(p):
    print("parquet not found:", p)
    raise SystemExit(1)

print("loading", p)
df = pd.read_parquet(p)
print("raw rows", len(df))
features = generate_features(df)
print("feature rows", len(features))
print(
    features[["close", "ma_5", "ma_10", "ma_20", "mom_10", "rsi_14"]].head().to_string()
)
# 保存特征文件
out = "db/market_data/600000.SH_1d.features.parquet"
features.to_parquet(out, engine="pyarrow")
print("saved features to", out)
