import base64
import datetime
import hashlib
import hmac
import json
import time
from urllib import parse

import akshare as ak
import pandas as pd
import requests

from Config import log, robot_id, secret


def record_log(msg, log_type='info', send=False):
    """
    记录日志
    :param msg: 日志信息
    :param log_type: 日志类型
    :return:
    """
    time_str = datetime.datetime.strftime(datetime.datetime.now(), "%H:%M:%S")
    log_msg = time_str + ' --> ' + msg
    print(log_msg)
    if log_type == 'info':
        log.info(msg=log_msg)
        if send:
            send_dingding_msg(log_msg, robot_id, secret)


def get_trading_price(value: dict):
    """
    获取下单的价格，如果没有指定返回0，即最新价下单
    :param value:
    :return:
    """
    if 'price' in value.keys():
        return value['price']
    else:
        return 0


def get_now_data(code):
    """
    获取最近日K线,详情参考股票基础课程构建数据库章节
    :param code:
    :return:
    """

    def requestForNew(url, max_try_num=10, sleep_time=5):
        headers = {
            'Referer': 'http://finance.sina.com.cn',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36 Edg/97.0.1072.62'
        }
        for i in range(max_try_num):
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                return response
            else:
                print("链接失败", response)
                time.sleep(sleep_time)

    url = "https://hq.sinajs.cn/list=" + code
    # =====抓取数据
    content = requestForNew(url).text  # 使用python自带的库，从网络上获取信息
    # =====将数据转换成DataFrame
    content = content.strip()  # 去掉文本前后的空格、回车等
    data_line = content.split('\n')  # 每行是一个股票的数据
    data_line = [i.replace('var hq_str_', '').split(',') for i in data_line]
    df = pd.DataFrame(data_line, dtype='float')  #

    # =====对DataFrame进行整理
    df[0] = df[0].str.split('="')
    df['股票代码'] = df[0].str[0].str.strip()
    df['股票名称'] = df[0].str[-1].str.strip()
    df['日期'] = df[30] + ' ' + df[31]  # 股票市场的K线，是普遍以当跟K线结束时间来命名的
    df['日期'] = pd.to_datetime(df['日期'])

    rename_dict = {1: '开盘价', 2: 'pre_close', 3: '收盘价', 4: '最高价', 5: '最低价', 6: '买1', 7: '卖1',
                   8: '成交量', 9: '成交额', 32: 'status'}
    # 其中amount单位是股，volume单位是元
    df.rename(columns=rename_dict, inplace=True)
    df = df[['股票代码', '日期', '开盘价', '最高价', '最低价', '收盘价']]
    return df


def get_day_candle(code, length=60):
    """
    获取最近的K线数据，数据源：网易，好处：有前收盘价
    :param code:
    :param length:
    :return:
    """
    code = code.split('.')[-1].lower() + code.split('.')[0]
    k_line = ak.stock_zh_a_daily(code, adjust='hfq')
    rename_dict = {
        'date': "交易日期",
        'open': "开盘价",
        'high': "最高价",
        'low': "最低价",
        'close': "收盘价",
        'volume': "成交量",
    }
    k_line.rename(columns=rename_dict, inplace=True)
    k_line = k_line[rename_dict.values()]
    return k_line


def calculate_order_quantity(code, order_volume):
    """
    处理下单股数
    :param code:
    :param order_volume:
    :return:
    """
    # 对科创板进行特殊处理
    if code[:2] == '68' and code[-2:] == 'SH':
        order_volume = int(order_volume)
        if order_volume < 200:
            print('金额过少，无法下单')
            return 0
    else:
        order_volume = int(order_volume / 100) * 100
        if order_volume < 100:
            return 0
    return order_volume


def stamp2time(stamp, utc=True):
    """
    处理时间戳
    :param stamp:
    :param utc:
    :return:
    """
    stamp_len = len(str(stamp))
    unit = {10: 's', 13: 'ms', 19: 'ns'}[stamp_len]
    if utc:
        local_time = pd.to_datetime(stamp, unit=unit) + pd.to_timedelta('8H')
    else:
        local_time = pd.to_datetime(stamp, unit=unit)
    return local_time


def cal_timestamp_sign(secret):
    # 根据钉钉开发文档，修改推送消息的安全设置https://ding-doc.dingtalk.com/doc#/serverapi2/qf2nxq
    # 也就是根据这个方法，不只是要有robot_id，还要有secret
    # 当前时间戳，单位是毫秒，与请求调用时间误差不能超过1小时
    # python3用int取整
    timestamp = int(round(time.time() * 1000))
    # 密钥，机器人安全设置页面，加签一栏下面显示的SEC开头的字符串
    secret_enc = bytes(secret.encode('utf-8'))
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    string_to_sign_enc = bytes(string_to_sign.encode('utf-8'))
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    # 得到最终的签名值
    sign = parse.quote_plus(base64.b64encode(hmac_code))
    return str(timestamp), str(sign)


def send_dingding_msg(content, robot_id,
                      secret=None):
    """
    :param content:
    :param robot_id:  你的access_token，即webhook地址中那段access_token。例如如下地址：https://oapi.dingtalk.com/robot/
    :param secret: 你的secret，即安全设置加签当中的那个密钥
    :return:
    """
    try:
        msg = {
            "msgtype": "text",
            "text": {"content": content + '\n' + datetime.datetime.now().strftime("%m-%d %H:%M:%S")}}
        headers = {"Content-Type": "application/json;charset=utf-8"}
        # https://oapi.dingtalk.com/robot/send?access_token=XXXXXX&timestamp=XXX&sign=XXX
        if secret:
            timestamp, sign_str = cal_timestamp_sign(secret)
            url = 'https://oapi.dingtalk.com/robot/send?access_token=' + robot_id + \
                  '&timestamp=' + timestamp + '&sign=' + sign_str
        else:
            url = 'https://oapi.dingtalk.com/robot/send?access_token=' + robot_id
        body = json.dumps(msg)
        requests.post(url, data=body, headers=headers, timeout=10)
        print('成功发送钉钉')
    except Exception as e:
        print("发送钉钉失败:", e)


def get_base_data(code):
    def requestForNew(url, max_try_num=10, sleep_time=5):
        headers = {
            'Referer': 'http://finance.sina.com.cn',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36 Edg/97.0.1072.62'
        }
        for i in range(max_try_num):
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                return response
            else:
                print("链接失败", response)
                time.sleep(sleep_time)

    # =====构建网址
    # 正常股票：sh600000 sz000002，退市股票：sh600002 sz000003、停牌股票：sz300124，除权股票：sh600276，上市新股：sz002952
    stock_code_list = [code]
    url = "https://hq.sinajs.cn/list=" + ",".join(stock_code_list)

    # =====抓取数据
    content = requestForNew(url).text  # 使用python自带的库，从网络上获取信息

    # =====将数据转换成DataFrame
    content = content.strip()  # 去掉文本前后的空格、回车等
    data_line = content.split('\n')  # 每行是一个股票的数据
    # print(data_line)
    # for i in data_line:
    #     i = i.replace('var hq_str_', '').split(',')
    #     print(i)
    data_line = [i.replace('var hq_str_', '').split(',') for i in data_line]
    df = pd.DataFrame(data_line)  #

    # =====对DataFrame进行整理
    df[0] = df[0].str.split('="')
    df['stock_code'] = df[0].str[0].str.strip()
    df['stock_name'] = df[0].str[-1].str.strip()
    df['candle_end_time'] = df[30] + ' ' + df[31]  # 股票市场的K线，是普遍以当跟K线结束时间来命名的
    df['candle_end_time'] = pd.to_datetime(df['candle_end_time'])

    rename_dict = {1: 'open', 2: 'pre_close', 3: 'close', 4: 'high', 5: 'low', 6: 'buy1', 7: 'sell1',
                   8: 'amount', 9: 'volume', 32: 'status'}  # 自己去对比数据，会有新的返现
    # 其中amount单位是股，volume单位是元
    df.rename(columns=rename_dict, inplace=True)
    df['status'] = df['status'].str.strip('";')
    df = df[
        ['stock_code', 'stock_name', 'candle_end_time', 'open', 'high', 'low', 'close', 'pre_close', 'amount', 'volume',
         'buy1', 'sell1', 'status']]

    return df['sell1'][0]


def check_order_volume(buy_code, order_volume, use_other_data):
    # 不足100
    if order_volume == 0:
        return False

    # 创业板不足200
    if use_other_data:
        if buy_code[2:].startswith('688') or buy_code[2:].startswith('300'):
            if order_volume < 200:
                return False
    else:
        if buy_code.startswith('688') or buy_code.startswith('300'):
            if order_volume < 200:
                return False

    return True


def transform_stock_code(code: str) -> str:
    return f"{code[2:]}.{code[:2].upper()}"