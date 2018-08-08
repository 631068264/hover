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
    tar_url = ''
    pair = 'btc_usdt'

    min_trade = 10
    price_point = 0.01
    amount_point = 0.000001


from dateutil import tz

tz_info = tz.gettz('Asia/Shanghai')
tz_local = tz.tzlocal()