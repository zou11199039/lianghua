from Function import *
from Config import *


def signal(mkt_df, para, **kwargs):
    # 获取股票代码
    code = kwargs["code"]

    if mkt_df.empty:
        msg = f"{code}数据为空"
        record_log(msg)
        return 0

    # 计算MACD
    mkt_df["EMA_short"] = mkt_df["收盘价"].ewm(span=para[0], adjust=False).mean()
    mkt_df["EMA_long"] = mkt_df["收盘价"].ewm(span=para[1], adjust=False).mean()
    mkt_df["DIF"] = mkt_df["EMA_short"] - mkt_df["EMA_long"]
    mkt_df["DEA"] = mkt_df["DIF"].ewm(span=para[2], adjust=False).mean()
    mkt_df["MACD"] = (mkt_df["DIF"] - mkt_df["DEA"]) * 2

    # 计算金叉
    con = mkt_df["MACD"] > 0
    con &= mkt_df["MACD"].shift(1) <= 0
    mkt_df.loc[con, "signal"] = 1

    # 计算死叉
    con = mkt_df["MACD"] < 0
    con &= mkt_df["MACD"].shift(1) >= 0
    mkt_df.loc[con, "signal"] = -1

    # 返回最后一行的信号,即最新的信号
    return mkt_df["signal"].iloc[-1]


def read_data(xtdata, code, **kwargs):
    try:
        # 获取日线数据
        mkt_df = get_day_candle(code)
        return mkt_df
    except:
        msg = f"获取数据出现问题，报错为：\n{traceback.format_exc()}"
        record_log(msg, send=True)
        return pd.DataFrame()
