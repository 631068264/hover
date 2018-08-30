#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author = 'wyx'
@time = 2017/2/4 09:05
@annotation = ''
"""
import calendar
import datetime
import decimal
import time

from dateutil import tz

from base import config


def error_msg():
    import traceback
    return traceback.format_exc()


def get_round(spread):
    if spread >= 1:
        return spread
    return decimal.Decimal(str(spread)).as_tuple().exponent * -1


def point2decfloat(point):
    """
    保留位数转化成decimal

    2 -> 0.01
    """
    if point >= 1:
        return decimal.Decimal('0.' + '0' * (point - 1) + '1')
    return safe_decimal(point)


def safe_decimal(data):
    if not isinstance(data, str):
        data = str(data)
    return decimal.Decimal(data)


def nowdt():
    return datetime.datetime.now(config.tz_info).replace(microsecond=0)


def dt2ts(dt, tzinfo=config.tz_info):
    if dt.tzinfo is None:
        if tzinfo is None:
            return int(time.mktime(dt.timetuple()))
        dt = dt.replace(tzinfo=tzinfo)
    utc_dt = dt.astimezone(tz.tzutc()).timetuple()
    return calendar.timegm(utc_dt)


def ts2dt(timestamp):
    if not isinstance(timestamp, float):
        timestamp = float(timestamp)
    return datetime.datetime.fromtimestamp(timestamp, config.tz_info)


def str2dt(dtstr, format='%Y-%m-%d %H:%M:%S', tzinfo=config.tz_info):
    dt = datetime.datetime.strptime(dtstr, format)
    return dt.replace(tzinfo=tzinfo)
