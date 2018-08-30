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


class ABCC_STAT(object):
    device_name = ABCC.device_name
    usdt_cny = 6.9
    # 推荐路径 l1_account=> l2_account=>mine_account l1 l2 位置无所谓
    mine_account = {
        'account': ABCC.account,
        'passwd': ABCC.passwd,
        'auth_key': ABCC.auth_key,
    }

    l1_account = {
        'account': '',
        'passwd': '',
        'auth_key': '',
    }
    l2_account = {
        'account': '',
        'passwd': '',
        'auth_key': '',
    }


class ABCC_ADDRESS(object):
    login_url = ABCC.login_url
    device_name = ABCC.device_name
    currency = 'eth'
    account_list = [
        {
            'account': ABCC.account,
            'passwd': ABCC.passwd,
            'auth_key': ABCC.auth_key,
        },
        {
            'account': '',
            'passwd': '',
            'auth_key': '',
        },

    ]


from dateutil import tz

tz_info = tz.gettz('Asia/Shanghai')
tz_local = tz.tzlocal()
