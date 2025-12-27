from Function import *
from Config import *
from utils.qmt_function import get_market_data


def signal(mkt_df, para, **kwargs):
    # 获取股票代码
    code = kwargs['code']
    if mkt_df.empty:
        msg = f'{code}数据为空'
        record_log(msg)
        return 0
    # 获取指定的价格
    specify_price = para[0]
    mkt_df['指定价格'] = specify_price
    # 如果最新价格大于指定价格即发出买入信号
    con = mkt_df['最新价'] > mkt_df['指定价格']
    mkt_df.loc[con, 'signal'] = 1

    # 如果最新价格小于指定价格即发出卖出信号
    con = mkt_df['最新价'] < mkt_df['指定价格']
    mkt_df.loc[con, 'signal'] = -1

    # 返回最后一行的信号,即最新的信号
    return mkt_df['signal'].iloc[-1]


def read_data(xtdata, code, **kwargs):
    try:
        # 获取逐笔数据
        mkt_df = get_market_data(xtdata, code, period='tick')
        return mkt_df
    except:
        msg = f'获取数据出现问题，报错为：\n{traceback.format_exc()}'
        record_log(msg, send=True)
        return pd.DataFrame()
