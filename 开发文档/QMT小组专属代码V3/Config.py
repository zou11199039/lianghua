import datetime
import os
import logging as log
import time
import traceback

from xtquant.xttrader import XtQuantTrader
from xtquant.xttype import StockAccount

# ========== 初始化 ==========
path = r"D:\中航证券QMT实盘-交易端\userdata_mini"  # 极简版QMT的路径
account_id = "010400007653"  # 资金账号

# 钉钉通知配置
robot_id = "c2cf554dc50538c817e25af82c48fb1ee1f817fc44f78fb3752e25267e7cab77"
secret = "SEC915d589c8dbb93dadd0e591835a3a41dec921ab6623e63efab2d7e361815b9ff"

session_id = int(
    time.time() * 1000
)  # session_id为会话编号，策略使用方对于不同的Python策略需要使用不同的会话编号（自己随便写）
xt_trader = XtQuantTrader(path, session_id)  # 创建API实例
user = StockAccount(account_id, "STOCK")  # 创建股票账户
# 启动交易线程
xt_trader.start()
# 建立交易连接，返回0表示连接成功
connect_result = xt_trader.connect()
# # 对交易回调进行订阅，订阅后可以收到交易主推，返回0表示订阅成功
subscribe_result = xt_trader.subscribe(user)

# ========== 初始化 ==========

root_path = os.path.dirname(os.path.abspath(__file__))
# region 发送日志相关
log_path = root_path + "/logs/"
log.basicConfig(
    filename=log_path + "%s_日志.log" % datetime.datetime.now().strftime("%Y-%m-%d"),
    level=log.INFO,
)
