#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author = 'wyx'
@time = 2018/8/9 15:08
@annotation = ''
"""
# 完成谷歌验证

import re

from appium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from base import config, util

host = 'localhost'
port = 4723
url = 'http://{host}:{port}/wd/hub'.format(host=host, port=port)

android_google_auth = {"deviceName": "", "appPackage": "com.google.android.apps.authenticator2",
                       "appActivity": "com.google.android.apps.authenticator.AuthenticatorActivity",
                       "platformName": "Android",
                       'automationName': 'uiautomator2',
                       "noReset": True}


def android_auth_code(device_name, tar_name, is_only=False, is_strict=True):
    def _clear_text(txt):
        return re.sub('\s', '', txt)

    def _is_swipe(user_list):
        start_x, start_y = user_list[-1].location['x'], user_list[-1].location['y']
        end_x, end_y = user_list[0].location['x'], user_list[0].location['y']
        before_page = driver.page_source
        driver.swipe(start_x, start_y, end_x, end_y)
        after_page = driver.page_source
        return before_page != after_page

    def _judge(tar, describe):
        if is_strict:
            return tar == describe
        return tar in describe

    android_google_auth['deviceName'] = device_name

    try:
        driver = webdriver.Remote(url, desired_capabilities=android_google_auth)
        wait = WebDriverWait(driver, 30)

        result = {}
        is_swipe = True
        while is_swipe:
            user_list_xpath = '//android.widget.ListView[@resource-id="com.google.android.apps.authenticator2:id/user_list"]/android.view.ViewGroup'
            user_list = wait.until(EC.presence_of_all_elements_located((
                By.XPATH, user_list_xpath)
            ))

            for u in user_list:
                describe = u.find_element_by_id('com.google.android.apps.authenticator2:id/current_user').text
                if _judge(_clear_text(tar_name).lower(), _clear_text(describe).lower()):
                    num = u.find_element_by_id('com.google.android.apps.authenticator2:id/pin_value').text
                    if is_only or is_strict:
                        return _clear_text(num)
                    result[_clear_text(describe)] = _clear_text(num)

            is_swipe = _is_swipe(user_list)

        driver.close_app()
        return result
    except:
        print(util.error_msg())
        return None


if __name__ == '__main__':
    print(android_auth_code(config.ABCC.device_name, config.ABCC.auth_key, is_strict=True))
