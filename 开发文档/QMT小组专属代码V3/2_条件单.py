import gc
import warnings

from xtquant import xtdata

from Config import xt_trader, user, subscribe_result, connect_result
from utils.qmt_function import *

warnings.filterwarnings('ignore')

if subscribe_result != 0 or connect_result != 0:
    record_log('链接或订阅失败，程序已退出', send=True)
    exit()
msg = f'{"=" * 40} 开始执行条件单 {"=" * 40}'
record_log(msg)

# 获取当前时间，作为一些条件获取数据的开始时间
start_time = datetime.datetime.now() - datetime.timedelta(minutes=10)
# 指定程序结束时间，默认为下午的三点三十分
run_end_time = datetime.datetime.strptime((datetime.datetime.now().strftime('%Y-%m-%d') + f' 15:30'), "%Y-%m-%d %H:%M")

# 定义订单的列表，列表的每个值都为一个字典，字典中为下单的具体条件
'''
买入:
    {'symbol': '603709.SH', 'amount': 2000, 'side': 'buy', 'fun': 'MACD', 'para': [12, 26, 9]}
        symbol：股票代码，格式必须为603709.SH
        amount： 买入金额
        side：方向 买入为buy
        fun：调用的方法，即conditions文件夹下的文件名
        para：生成买入、卖出信号的参数
        
卖出：
    {'symbol': '600006.SH', 'volume': 100, 'side': 'sell', 'fun': '突破阈值', 'para': [5.82]},
        symbol：股票代码，格式必须为603709.SH
        volume：卖出的数量，单位为股数
        side：方向 卖出为sell
        fun：调用的方法，即conditions文件夹下的文件名
        para：生成买入、卖出信号的参数
'''
order_list = [
    {'symbol': '603709.SH', 'amount': 2000, 'side': 'buy', 'fun': 'MACD', 'para': [12, 26, 9]},
    {'symbol': '002719.SZ', 'amount': 2000, 'side': 'buy', 'fun': '触碰均线', 'para': [2]},
    # {'symbol': '000521.SZ', 'volume': 2000, 'side': 'sell', 'fun': '突破阈值', 'para': [4.4]},
    {'symbol': '600006.SH', 'volume': 100, 'side': 'sell', 'fun': '突破阈值', 'para': [5.82]},
    {'symbol': '600000.SH', 'volume': 2000, 'side': 'sell', 'fun': '止盈止损', 'para': [-0.03, 0.013]},
    {'symbol': '688555.SH', 'amount': 2000, 'side': 'buy', 'fun': '反弹下单', 'para': [0.002]},
]
# 获取所有交易的股票代码
all_code_list = list(set([i['symbol'] for i in order_list]))
# 订阅并补全需要交易股票代码的数据
subscription_data(xtdata, all_code_list, 'tick', start_time=start_time)

# 开始循环监测股票代码
while True:
    for index, value in enumerate(order_list):
        # 获取股票代码
        code = value['symbol']
        record_log(f'监测{code},条件:{value["fun"]},参数:{value["para"]},交易方向:{value["side"]}')
        # 动态导入对应的py文件
        # __import__ 动态导入模块。详情请见：https://www.runoob.com/python/python-func-__import__.html
        cls = __import__('conditions.%s' % value['fun'], fromlist=('',))  # fromlist如果为空，导入的是factors包，所以需要给factors传入参数
        # 读取数据
        mkt_df = getattr(cls, 'read_data')(xtdata, code, start_time=start_time)
        # 计算交易的信号
        signal = getattr(cls, 'signal')(mkt_df, value['para'], xt_trader=xt_trader, user=user, code=code)
        # 删除数据，清理内存占用
        del mkt_df
        gc.collect()
        # 如果信号为1，并且本次循环的股票交易方向为买入 即进行交易
        if (signal == 1) and (value['side'] == 'buy'):
            # 获取盘口数据
            mkt_data = get_tick(xtdata, code)
            # 根据最新价与指定的买入金额计算买入的股数
            order_volume = value['amount'] // mkt_data['最新价']
            # 进行买入
            buy_stock(xt_trader, user, code, order_volume, strategy_name=f'{code}{value["fun"]}买入')
            # 下单后删除对应的数据
            del order_list[index]
        #  如果信号为-1，并且本次循环的股票交易方向为卖出 即进行交易
        elif (signal == -1) and (value['side'] == 'sell'):
            # 获取卖出的股数
            order_volume = value['volume']
            # 进行卖出
            sell_stock(xt_trader, user, code, order_volume,
                       strategy_name=f'{code}{value["fun"]}卖出')
            # 下单后删除对应的数据
            del order_list[index]
        else:
            record_log(f'{code}无信号，继续等待')
        # 如果order_list为空，证明所有交易已成交，退出程序
        if not order_list:
            record_log('程序已完成全部下单，程序退出', send=True)
            exit()
        time.sleep(1)
    # 如果现在的时间大于指定的结束时间，退出程序
    if datetime.datetime.now() > run_end_time:
        record_log('程序已运行至指定结束时间，程序退出', send=True)
        exit()
