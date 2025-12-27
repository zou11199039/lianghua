from Function import *
from Config import *
from utils.qmt_function import testing_position, get_market_data


def signal(mkt_df, para, **kwargs):
    # 获取股票代码
    code = kwargs['code']
    xt_trader = kwargs['xt_trader']
    user = kwargs['user']
    if len(para) < 2 or mkt_df.empty:
        msg = f'参数长度小于2或者{code}数据为空'
        record_log(msg)
        return 0
    # 获取止盈比例
    stop_profit = max(para)
    # 获取止损比例
    stop_loss = min(para)
    # 获取持仓
    pos_res = testing_position(xt_trader, user, code)
    if not pos_res or pos_res.can_use_volume < 0:
        print('无持仓或持仓不足，无法卖出')
        return None
    # 获取最新的价格
    now_price = mkt_df.iloc[-1]['最新价']
    # 现在的价格 / 开仓的价格 - 1     即持仓收益
    profit = now_price / pos_res.open_price - 1
    # 如果持仓收益大于止盈比例或者小于止损比例  发出平仓信号
    if profit >= stop_profit or profit <= stop_loss:
        return -1


def read_data(xtdata, code, **kwargs):
    try:
        mkt_df = get_market_data(xtdata, code, period='tick')
        return mkt_df
    except:
        msg = f'获取数据出现问题，报错为：\n{traceback.format_exc()}'
        record_log(msg, send=True)
        return pd.DataFrame()
