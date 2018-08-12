#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author = 'wyx'
@time = 2018/8/11 20:23
@annotation = ''
"""
import datetime
import io
import json

import pandas as pd
import requests as req
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from base import config, logger, util
from google_auth import android_auth_code

NOW_DATE = str((util.nowdt() - datetime.timedelta(days=2)).date())


mine_profit_url_json = 'https://abcc.com/history/minings.json?page=1&per_page=20'
csv_url = 'https://abcc.com/history/trades.csv?per_page=1000&from={date} 00:00:00&to={date} 23:59:00'.format(
    date=NOW_DATE)

driver = webdriver.Chrome()

logger.AutoLog.log_path = 'logs'
strategy_id = 'abcc_stat'
log = logger.AutoLog.file_log(strategy_id)
conf = config.ABCC_STAT
USDT_CNY = util.safe_decimal(conf.usdt_cny)


class AT_STAT(object):
    amount = 0

    def _login(self, account_info):
        account = account_info['account']
        passwd = account_info['passwd']
        auth_key = account_info['auth_key']
        try:
            wait = WebDriverWait(driver, 500)
            driver.get(conf.login_url)

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

    def _stat(self, account_info):
        amount = 0
        is_ok = self._login(account_info)
        if is_ok:
            self._get_request_kw()
            driver.get(mine_profit_url_json)
            rep = req.get(mine_profit_url_json, **self.req_kw)
            stat_data = rep.json()
            for d in stat_data['minings']:
                real_create_time = json.loads(d['extra_info'])['created_at']
                if NOW_DATE in real_create_time:
                    amount += util.safe_decimal(d['amount'])

        driver.delete_all_cookies()
        return amount

    def get_fee(self):
        content = req.get(csv_url, **self.req_kw).content
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        fee = 0
        try:
            df['手续费'] = df['手续费'].astype('float64')
            fee = df['手续费'].sum()
        except KeyError:
            df['Fee'] = df['Fee'].astype('float64')
            fee = df['Fee'].sum()

        return util.safe_decimal(fee)

    def run(self):
        mine_amount = self._stat(conf.mine_account)

        fee = self.get_fee()

        invite_amount_1 = self._stat(conf.l1_account)
        invite_amount_2 = self._stat(conf.l2_account)

        total_amount = mine_amount + invite_amount_1 + invite_amount_2

        log.info('{} 挖矿总量 {} 手续费 {} USDT 成本 {} CNY'.format(NOW_DATE, total_amount, fee,
                                                           fee / total_amount * USDT_CNY if total_amount > 0 else 0))

        driver.close()
        return total_amount


if __name__ == '__main__':
    AT_STAT().run()
