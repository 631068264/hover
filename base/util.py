#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author = 'wyx'
@time = 2017/2/4 09:05
@annotation = ''
"""
import decimal


def error_msg():
    import traceback
    return traceback.format_exc()


def get_round(spread):
    if spread >= 1:
        return spread
    return decimal.Decimal(str(spread)).as_tuple().exponent * -1


def safe_decimal(data):
    if not isinstance(data, str):
        data = str(data)
    return decimal.Decimal(data)
