#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author = 'wyx'
@time = 2018/8/11 20:23
@annotation = ''
"""

import requests as req
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from base import config, logger, util
from base.stash import Stash
from base.google_auth import android_auth_code

conf = config.ABCC_ADDRESS
driver = webdriver.Chrome()

logger.AutoLog.log_path = 'logs'
strategy_id = 'abcc_address_{}'.format(conf.currency)
log = logger.AutoLog.file_log(strategy_id)

address_url = 'https://abcc.com/funds/payment_address?currency={}'.format(conf.currency)


class Address(object):

    def _dialog_close(self):
        wait = WebDriverWait(driver, 5)
        try:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'dialog-content')))
        except:
            return
        driver.find_element_by_css_selector('.iconfont.icon-guanbi').click()

    def _set_zh(self):
        # 中文
        driver.get(conf.login_url)
        driver.add_cookie({
            'name': 'lang',
            'value': 'zh-CN',
        })

    def _login(self, account_info):
        self._set_zh()

        account = account_info['account']
        passwd = account_info['passwd']
        auth_key = account_info['auth_key']
        try:
            wait = WebDriverWait(driver, 500)
            driver.get(conf.login_url)

            self._dialog_close()

            account_ele = wait.until(EC.presence_of_element_located((By.NAME, 'auth_key')))
            account_ele.clear()
            account_ele.send_keys(account)

            passwd_ele = wait.until(EC.presence_of_element_located((By.NAME, 'password')))
            passwd_ele.clear()
            passwd_ele.send_keys(passwd)

            driver.find_element_by_id('submit').click()

            print('输入二次验证码')
            if conf.device_name and auth_key:
                auth_input = wait.until(EC.presence_of_element_located((
                    By.XPATH, '//div[@class="google-input"]/div/input'
                )))
                flag = True
                while flag:
                    code = android_auth_code(conf.device_name, auth_key)
                    if code:
                        auth_input.clear()
                        auth_input.send_keys(code)
                        try:
                            WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.CLASS_NAME, 'warn')))
                        except:
                            flag = False

            element = WebDriverWait(driver, 500).until(EC.title_contains("个人中心"))
            return True

        except:
            log.error(util.error_msg())
            return False

    def _get_cookies(self):
        cookies = driver.get_cookies()
        return {cookie['name']: cookie['value'] for cookie in cookies}

    def _get_user_agent(self):
        selenium_user_agent = driver.execute_script("return navigator.userAgent;")
        return {"user-agent": selenium_user_agent}

    def _get_request_kw(self):
        self.req_kw = {'cookies': self._get_cookies(), 'headers': self._get_user_agent()}
        return self.req_kw

    def _address(self, account_info, stash):
        if stash.get(account_info['account'], None):
            return stash[account_info['account']]

        is_ok = self._login(account_info)
        if is_ok:
            try:
                rep = req.get(address_url, **self._get_request_kw())
                data = rep.json()
                if data['payment_address']['currency'] == conf.currency:
                    deposit_address = data['payment_address']['deposit_address']
                    stash[account_info['account']] = deposit_address
                    return deposit_address
            except:
                log.error(util.error_msg())

    def run(self):
        address_list = []
        with Stash(strategy_id) as stash:
            for account_info in conf.account_list:
                address = self._address(account_info, stash)
                log.info('{} [{}]'.format(account_info['account'], address))
                driver.delete_all_cookies()
                if address:
                    address_list.append(address)

        with open('{}.txt'.format(strategy_id), 'w') as f:
            f.write(','.join(address_list))

        driver.close()


if __name__ == '__main__':
    Address().run()
