#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author = 'wyx'
@time = 2017/2/3 16:12
@annotation = ''
"""


class ABCC(object):
    account = ''
    passwd = ''

    login_url = 'https://abcc.com/signin'
    # 交易目标
    tar_url = ''
    pair = 'btc_usdt'

    # 最小交易额
    min_trade = 10
    # 最小小数位
    price_point = 0.01
    amount_point = 0.000001

    # Google Auth android
    auto_auth = False
    auth_key = ''
    device_name = ''


from dateutil import tz

tz_info = tz.gettz('Asia/Shanghai')
tz_local = tz.tzlocal()
