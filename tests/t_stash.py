#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author = 'wyx'
@time = 2018/8/10 11:43
@annotation = ''
"""

from base.stash import Stash

with Stash('abcc_eth_btc') as stash:
    print(stash['mode'])

# dt = util.ts2dt(time.time())
# print(dt)
# ts = util.dt2ts(dt)
# print(ts)
#
# print(((util.nowdt()-(util.nowdt()-datetime.timedelta(days=1)))).days)
#
#
# print('{:.4f}'.format(util.safe_decimal(12.99)))
