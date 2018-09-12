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
import json
import re
import subprocess
import sys
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


def get_point(num):
    return decimal.Decimal(str(num)).as_tuple().exponent * -1


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


def deal_min_trade(min_trade):
    if min_trade >= 1 and isinstance(min_trade, int):
        return min_trade + 1
    else:
        point = get_point(min_trade)
        return min_trade + float(point2decfloat(point))


def shell_cmd(cmd):
    return subprocess.check_output(cmd, stderr=sys.stderr, shell=True)


def android_activity(json_output=False):
    def device_name():
        cmd = 'adb devices -l'
        r = shell_cmd(cmd).decode()
        res = re.search(r'model:(.*?) device', r, re.S)
        if res:
            return {'deviceName': res.groups()[0]}
        return None

    def get_package():
        """get the current activity and packagename"""
        cmd = 'adb shell dumpsys window windows | grep -E "mCurrentFocus"'
        r = shell_cmd(cmd).decode()

        res = re.search(r'=Window{(.*?)}', r)
        if res:
            try:
                res = res.groups()[0].split(' ')[-1].split('/')
                package_name = res[0]
                activity_name = res[1]
                if package_name and activity_name:
                    return {
                        'appPackage': package_name,
                        'appActivity': activity_name,
                    }
                return None
            except Exception:
                return None

    device = device_name()
    if device is None:
        raise RuntimeError('No device or adb')
    tar_package = get_package()
    # if tar_package is None:
    #     raise RuntimeError('No current activity')
    if tar_package:
        device.update(tar_package)
        device['platformName'] = 'Android'
        device['noReset'] = True
        device['automationName'] = 'uiautomator2'
        device['newCommandTimeout'] = 0
        return device if not json_output else json.dumps(device)


def project_dir():
    import os
    file_path = os.path.abspath(__file__)
    return os.path.dirname(os.path.dirname(file_path))
