from Config import *
from Function import *


def signal(mkt_df, para, **kwargs):
    # 获取股票代码
    code = kwargs["code"]
    if mkt_df.empty:
        msg = f"{code}数据为空"
        record_log(msg)
        return 0
    # 计算均线
    mkt_df["MA"] = mkt_df["收盘价"].rolling(para[0], min_periods=1).mean()
    # 上穿均线买入
    con = mkt_df["收盘价"] > mkt_df["MA"]
    con &= mkt_df["收盘价"].shift(1) <= mkt_df["MA"]
    mkt_df.loc[con, "signal"] = 1

    # 下穿均线卖出
    con = mkt_df["收盘价"] < mkt_df["MA"]
    con &= mkt_df["收盘价"].shift(1) >= mkt_df["MA"]
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
