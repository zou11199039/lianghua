from xtquant import xtdata

from Config import *
from Function import *
from utils.qmt_function import sell_stock, get_tick, buy_stock

# 定义买入卖出的字典
"""
 {
    '600006.SH': {'amount': 1000, 'price': 5},
    '600000.SH': {'amount': 1500},
}
键名：股票代码
price：买入、卖出价格，如果不指定默认为最新价
买入：
    amount：买入金额
卖出：
    volume：卖出股数

"""
buy_order_dict = {
    # '600006.SH': {'amount': 1000, 'price': 5},
    # '600000.SH': {'amount': 1500},
    '000413.SZ': {'amount': 200}
}
sell_order_dict = {
    '600006.SH': {'volume': 100},
}
if subscribe_result != 0 or connect_result != 0:
    record_log('链接或订阅失败，程序已退出', send=True)
    exit()
msg = f'{"=" * 40} 开始执行批量买入卖出 {"=" * 40}'
record_log(msg)

# 循环进行卖出
for sell_code, sell_value in sell_order_dict.items():
    # 获取卖出价格
    close_price = get_trading_price(sell_value)
    # 进行卖出
    sell_stock(xt_trader, user, sell_code, sell_value['volume'], close_price)

# 循环进行买入
for buy_code, buy_value in buy_order_dict.items():
    # 使用其他源
    use_other_data = False
    # 获取下单金额
    amount = buy_value['amount']
    # 获取下单价格
    open_price = get_trading_price(buy_value)
    if open_price == 0:
        fix_price = False
        open_price = get_tick(xtdata, buy_code)
        if not open_price:
            buy_code = buy_code[7:].lower() + buy_code[0:6]
            open_price = get_base_data(buy_code)
            use_other_data = True
        else:
            open_price = float(open_price['最新价'])
    else:
        fix_price = True
    # 计算下单量
    order_volume = amount // float(open_price)
    # 修正下单量
    order_volume = (order_volume // 100) * 100
    # 检查下单量是否合规
    can_buy = check_order_volume(buy_code, order_volume, use_other_data)
    # 可以买就下单, 如果用了其他数据源则要用最新价修正下单, 为了加速成单使用卖1价买入
    if can_buy:
        if use_other_data:
            buy_code = transform_stock_code(buy_code)
            buy_stock(xt_trader, user, buy_code, order_volume, price=0)
        else:
            if fix_price:
                buy_stock(xt_trader, user, buy_code, order_volume, open_price)
            else:
                buy_stock(xt_trader, user, buy_code, order_volume, price=0)

    else:
        msg = f'=====买入失败=====\n股票代码：{buy_code}\n' + f"{buy_code}下单量不满足最小购买"
        record_log(msg, send=True)
