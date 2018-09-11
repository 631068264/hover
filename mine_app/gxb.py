#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author = 'wyx'
@time = 2018/8/5 11:30
@annotation = ''
"""
import json

from appium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

host = 'localhost'
port = 4723
url = 'http://{host}:{port}/wd/hub'.format(host=host, port=port)
desired_caps = {'deviceName': 'ONEPLUS_A5000', 'appPackage': 'com.gxb.wallet.app',
                'appActivity': 'com.gxb.sdk.activity.WalletHomeActivity', 'platformName': 'Android', 'noReset': True,
                'automationName': 'uiautomator2', 'newCommandTimeout': 0}

xpath = '//android.view.View[@resource-id="area"]/android.view.View'
print(json.dumps(desired_caps))

class GXB(object):

    def __init__(self):
        self.driver = webdriver.Remote(url, desired_capabilities=desired_caps)
        self.wait = WebDriverWait(self.driver, 5)

    def run(self):
        while True:
            try:
                area_ele = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
                view_len = len(area_ele)
                view_invalid = 0
                for view in area_ele:
                    if view.find_element_by_xpath('.//android.view.View/android.view.View[1]').text:
                        view.click()
                    else:
                        view_invalid += 1

                if view_len == view_invalid:
                    return self.close()
            except:
               return self.close()

    def close(self):
        self.driver.close_app()
        return True


if __name__ == '__main__':
    GXB().run()
