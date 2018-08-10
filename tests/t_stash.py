#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author = 'wyx'
@time = 2018/8/10 11:43
@annotation = ''
"""
from base.stash import Stash

with Stash('abcc_btc_usdt') as stash:
    print(stash['mode'])
