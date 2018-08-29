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

NOW_DATE = str((util.nowdt() - datetime.timedelta(days=1)).date())
day_limit = (util.nowdt() - util.str2dt(NOW_DATE, format='%Y-%m-%d')).days

mine_profit_url_json = 'https://abcc.com/history/minings.json?page=1&per_page=50'
csv_url = 'https://abcc.com/history/trades.csv?per_page=1000&from={date} 00:00:00&to={date} 23:59:00'.format(
    date=NOW_DATE)
kline_url = 'https://abcc.com/api/v2/k.json?market=atusdt&limit={}&period=1440'.format(day_limit)

driver = webdriver.Chrome()

logger.AutoLog.log_path = 'logs'
strategy_id = 'abcc_stat'
log = logger.AutoLog.file_log(strategy_id)
conf = config.ABCC_STAT
USDT_CNY = util.safe_decimal(conf.usdt_cny)


class AT_STAT(object):
    amount = 0

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

    def _stat(self, account_info, is_exit=True):
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
        if is_exit:
            driver.delete_all_cookies()
        return amount

    def get_fee(self):
        content = req.get(csv_url, **self.req_kw).content
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        fee = 0
        volume = 0
        try:
            df[['手续费', '金额']] = df[['手续费', '金额']].astype('float64')
            fee = df['手续费'].sum()
            volume = df['金额'].sum()
        except KeyError:
            df[['Fee', 'Amount']] = df[['Fee', 'Amount']].astype('float64')
            fee = df['Fee'].sum()
            volume = df['Amount'].sum()

        return util.safe_decimal(fee), util.safe_decimal(volume), df.shape[0]

    def get_price(self):
        """
        收矿日收盘价

        9-10 挖的矿 9-11收到 获取9-11收盘价
        """
        kline = req.get(kline_url, **self.req_kw).json()
        return util.safe_decimal(kline[0][4])

    def run(self):
        mine_amount = self._stat(conf.mine_account, is_exit=False)
        fee, volume, trade_count = self.get_fee()
        price = self.get_price()
        driver.delete_all_cookies()

        invite_amount_1 = self._stat(conf.l1_account)
        invite_amount_2 = self._stat(conf.l2_account)

        total_amount = mine_amount + invite_amount_1 + invite_amount_2
        at_cost = fee / total_amount if total_amount > 0 else 0
        change = 1 - at_cost / price
        profit = (price - at_cost) * total_amount
        log.info(NOW_DATE)
        log.info('挖矿总量 {:.4f} 手续费 {:.4f} USDT 成本 {:.2f} CNY 盈利 {:.2%} {:.2f} CNY'.format(
            total_amount, fee, at_cost * USDT_CNY, change, profit * USDT_CNY))
        log.info('成交次数 {} 成交量 {:.2f}'.format(trade_count, volume))

        driver.close()
        return total_amount


if __name__ == '__main__':
    AT_STAT().run()
