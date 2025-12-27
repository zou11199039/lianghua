import datetime
import time

import pandas as pd
from xtquant import xtconstant
from xtquant.xtdata import subscribe_quote
from xtquant.xtdata import get_market_data as gmd
from Function import calculate_order_quantity, record_log, stamp2time


def buy_stock(xt_trader, user, code, order_volume, price=0, **kwargs):
    """
    进行买入的函数
    :param xt_trader:
    :param user:
    :param code: 下单股票代码
    :param order_volume: 下单股数
    :param price: 下单价格
    :param kwargs: 其他参数
    :return:
    """
    subscribe_quote(code, period='tick', start_time='', count=-1, callback=None)
    for _ in range(5):
        try:
            # 处理下单的股数
            order_volume = calculate_order_quantity(code, order_volume)
            # 如果下单股数为0直接退出
            if order_volume == 0:
                msg = f'=====买入失败=====\n{code}：下单数量等于0'
                record_log(msg, send=True)
                return True
            # 下单价格为0时按照最新价下单
            if price == 0:
                df = gmd(field_list=['askPrice'], stock_list=[code], period='tick', start_time='', count=-1)
                price = df[code][-1][0][0]
                price_type = xtconstant.FIX_PRICE
            # 下单价格非0时按照限价下单
            else:
                price_type = xtconstant.FIX_PRICE
            msg = f'=====开始买入=====\n买入股票{code}，报价类型：{price_type_dict.get(price_type, "")}，下单数量：{order_volume}，下单价格：{price}'
            record_log(msg, send=True)
            # 调用QMT下单接口
            order_id = xt_trader.order_stock(user, code, xtconstant.STOCK_BUY, order_volume, price_type, price,
                                             **kwargs)
            if order_id > 0:
                # 获取订单状态
                order_dict = entrustment_details(xt_trader, user, order_id)
                msg = f'=====买入完成=====\n订单号：{order_id}'
                for k, v in order_dict.items():
                    msg += f'，{k}：{v}'
                record_log(msg, send=True)
                return True
            else:
                msg = f'=====买入失败=====\n股票代码：{code}'
                record_log(msg)
                raise Exception(msg)
        except Exception as e:
            pass
    msg = f'=====买入失败=====\n股票代码：{code}'
    record_log(msg, send=True)


def sell_stock(xt_trader, user, code, sell_volume, price=0, **kwargs):
    """
    进行卖出的函数
    :param xt_trader:
    :param user:
    :param code: 股票代码
    :param sell_volume: 卖出股数
    :param price: 卖出价格
    :param kwargs: 其他参数
    :return:
    """
    subscribe_quote(code, period='tick', start_time='', count=-1, callback=None)
    for _ in range(5):
        try:
            # 获取对应股票的持仓量
            pos_res = testing_position(xt_trader, user, code)
            # 如果无持仓或者可用持仓量小于0即无法卖出.直接退出函数
            if not pos_res or pos_res.can_use_volume <= 0:
                msg = f'{code}无持仓，无法卖出'
                record_log(msg, send=True)
                return True
            # 处理下单股数
            order_volume = calculate_order_quantity(code, sell_volume)
            # 当指定的卖出股数小于持仓量:卖出股数为指定的数量
            # 当指定的卖出股数大于持仓量:卖出所有持仓
            order_volume = pos_res.can_use_volume if pos_res.can_use_volume < order_volume else order_volume
            # 如果处理后的卖出股数为0,直接退出程序
            if order_volume == 0:
                msg = f'=====卖出失败=====\n{code}：下单数量等于0'
                record_log(msg, send=True)
                return True
            # 下单价格为0时按照最新价下单
            if price == 0:
                df = gmd(field_list=['bidPrice'], stock_list=[code], period='tick', start_time='', count=-1)
                price = df[code][-1][0][0]
                price_type = xtconstant.FIX_PRICE
            # 下单价格非0时按照限价下单
            else:
                price_type = xtconstant.FIX_PRICE
            msg = f'=====开始卖出=====\n卖出股票{code}，报价类型{price_type_dict.get(price_type, "")}，下单数量：{order_volume}，下单价格：{price}'
            record_log(msg)
            # 调用QMT下单接口
            order_id = xt_trader.order_stock(user, code, xtconstant.STOCK_SELL, order_volume, price_type, price,
                                             **kwargs)
            if order_id > 0:
                # 获取订单状态
                order_dict = entrustment_details(xt_trader, user, order_id)
                msg = f'=====卖出完成=====\n订单号：{order_id}'
                for k, v in order_dict.items():
                    msg += f'，{k}：{v}'
                record_log(msg, send=True)
                return True
            else:
                msg = f'=====卖出失败=====\n股票代码：{code}'
                record_log(msg)
                raise Exception(msg)
        except:
            pass
    msg = f'=====卖出失败=====\n股票代码：{code}'
    record_log(msg)


def entrustment_details(xt_trader, user, order_id):
    """
    根据订单id获取订单状态
    :param xt_trader:
    :param user:
    :param order_id:
    :return:
    """
    # 因为QMT获取订单状态会有一些延迟,所有我们多试几次
    for _ in range(5):
        try:
            # 调用QMT接口获取订单状态
            order = xt_trader.query_stock_order(user, order_id)
            # 对返回数据进行解析并返回
            return {
                '订单编号': order.order_id,
                '订单备注': order.order_remark,
                '委托状态': order_status_type_dict.get(order.order_status, ''),
                '柜台合同编号': order.order_sysid,
                '报单时间': str(datetime.datetime.fromtimestamp(order.order_time)),
                '委托数量': order.order_volume,
                '委托价格': order.price,
                '成交数量': order.traded_volume,
                '成交均价': order.traded_price,
                '策略名称': order.strategy_name,
            }
        except:
            time.sleep(1)
            pass
    # 如果重试全部失败返回空的数据
    return {
        '订单编号': '',
        '订单备注': '',
        '委托状态': '',
        '柜台合同编号': '',
        '报单时间': '',
        '委托数量': '',
        '委托价格': '',
        '成交数量': '',
        '成交均价': '',
        '策略名称': '',
    }


def testing_position(xt_trader, user, code=None):
    """
    获取当前持仓
    :param xt_trader:
    :param user:
    :param code:
    :return:
    """
    if code:
        return xt_trader.query_stock_position(user, code)
    return xt_trader.query_stock_positions(user)


def subscription_data(xtdata, code_list, period, count=1000, **kwargs):
    """
    订阅数据并补充历史数据
    :param xtdata:
    :param code_list:
    :param period:
    :param count:
    :param kwargs:
    :return:
    """
    # 获取开始时间
    if 'start_time' in kwargs.keys():
        start_time = kwargs['start_time'].strftime('%Y%m%d%H%M%S') + '00'
    else:
        start_time = datetime.date.today().strftime('%Y%m%d') + '093000'
    # 循环处理所有股票
    for code in code_list:
        # 订阅数据
        xtdata.subscribe_quote(code, period, count=count)
        # 设置结束时间.即当天下午3点
        end_time = datetime.date.today().strftime('%Y%m%d') + '150000'
        # 下载历史数据
        xtdata.download_history_data(code, period='tick', start_time=start_time, end_time=end_time)


def get_market_data(xtdata, code, period, before_open=False, drop_0=True):
    if before_open:
        start = datetime.date.today().strftime('%Y%m%d') + '091500'
    else:
        start = datetime.date.today().strftime('%Y%m%d') + '093000'
    end = datetime.date.today().strftime('%Y%m%d') + '153000'
    mkt_data = pd.DataFrame(xtdata.get_market_data([], [code], period='tick', start_time=start, end_time=end)[code])
    rename_dict = {'time': '时间', 'lastPrice': '最新价', 'open': '开盘价', 'high': '最高价', 'low': '最低价',
                   'lastClose': '前收盘价', 'amount': '成交额', 'volume': '成交量', 'askPrice': '委卖价',
                   'bidPrice': '委买价',
                   'askVol': '委卖量', 'bidVol': '委买量'}
    mkt_data = mkt_data[list(rename_dict.keys())].rename(columns=rename_dict)
    mkt_data['时间'] = mkt_data['时间'].apply(stamp2time)

    if drop_0:  # 处理没有成交记录的情况
        mkt_data = mkt_data[mkt_data['成交额'] > 0].reset_index(drop=True)
    if mkt_data.empty:
        return mkt_data
    if period != 'tick':
        if period == 'open2now':
            mkt_data = {'时间': mkt_data['时间'].iloc[-1],
                        '最新价': mkt_data['最新价'].iloc[-1],
                        '开盘价': mkt_data['开盘价'].iloc[0],
                        '最高价': mkt_data['最高价'].max(),
                        '最低价': mkt_data['最低价'].min(),
                        '前收盘价': mkt_data['前收盘价'].iloc[0],
                        '成交额': mkt_data['成交额'].sum(),
                        '成交量': mkt_data['成交量'].sum()}
        else:
            resample_dict = {'时间': 'first', '最新价': 'last', '开盘价': 'first', '最高价': 'max', '最低价': 'min',
                             '成交额': 'sum',
                             '成交量': 'sum'}
            mkt_data = mkt_data.resample(rule=period, on='时间').agg(resample_dict).reset_index(drop=True)
    return mkt_data


def get_tick(xtdata, code_list):
    """
    获取盘口数据
    :param xtdata:
    :param code_list:
    :return:
    """
    if not isinstance(code_list, list):
        code_list = [code_list]
    res = xtdata.get_full_tick(code_list)
    ticks = {}
    for code, item in res.items():
        tick = {}
        rename_dict = {'timetag': '时间', 'lastPrice': '最新价', 'open': '开盘价', 'high': '最高价', 'low': '最低价',
                       'lastClose': '前收盘价', 'amount': '成交额', 'volume': '成交量', 'stockStatus': '状态',
                       'askPrice': '委卖价', 'bidPrice': '委买价', 'askVol': '委卖量', 'bidVol': '委买量'}
        for key, value in rename_dict.items():
            tick[value] = item[key]
        ticks[code] = tick
    if len(ticks) == 1:
        ticks = ticks[code_list[0]]
    return ticks


# 订单状态
order_status_type_dict = {
    48: '未报',
    49: '待报',
    50: '已报',
    51: '已报待撤',
    52: '部成待撤',
    53: '部撤',
    54: '已撤',
    55: '部成',
    56: '已成',
    57: '已成',
    255: '未知',
}

# 下单类型
price_type_dict = {
    5: '最新价',
    11: '限价',
}
