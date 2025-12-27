from Config import *
from Function import *
from utils.qmt_function import get_market_data


def signal(mkt_df, para, **kwargs):
    # 获取股票代码
    code = kwargs['code']

    if mkt_df.empty:
        msg = f'{code}数据为空'
        record_log(msg)
        return 0

    # 获取指定的参数,即反弹的阈值
    threshold = para[0]
    # 获取指定时间至今的最低价
    mkt_df['至今最低价'] = mkt_df['最新价'].expanding().min()
    # 最低价*(1+阈值)即为开仓价格
    mkt_df['开仓价格'] = mkt_df['至今最低价'] * (1 + threshold)
    # 当最新价大于开仓价格时即为反弹,发出买入信号
    con = mkt_df['最新价'] > mkt_df['开仓价格']
    mkt_df.loc[con, 'signal'] = 1

    # 获取指定时间至今的最高价
    mkt_df['至今最高价'] = mkt_df['最新价'].expanding().max()
    # 最高价*(1-阈值)即为卖出价格
    mkt_df['卖出价格'] = mkt_df['至今最高价'] * (1 - threshold)
    # 当最新价小于卖出价格时即为回落,发出卖出信号
    con = mkt_df['最新价'] < mkt_df['卖出价格']
    mkt_df.loc[con, 'signal'] = -1

    # 返回最后一行的信号,即最新的信号
    return mkt_df['signal'].iloc[-1]


def read_data(xtdata, code, **kwargs):
    try:
        # 获取指定的数据开始时间
        start_time = kwargs['start_time']
        # 获取逐笔数据
        mkt_df = get_market_data(xtdata, code, period='tick', before_open=True)
        return mkt_df
    except:
        msg = f'获取数据出现问题，报错为：\n{traceback.format_exc()}'
        record_log(msg, send=True)
        return pd.DataFrame()
