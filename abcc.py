#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author = 'wyx'
@time = 2018/8/7 14:34
@annotation = ''
"""

# http = 'http://localhost:8087'
# https = 'https://localhost:8087'
# os.environ['HTTP_PROXY'] = http
# os.environ['HTTPS_PROXY'] = https

import decimal
import random
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from base import config, logger, util, const

logger.AutoLog.log_path = 'logs'
log = logger.AutoLog.file_log('abcc_{}'.format(config.ABCC.pair.lower()))

# options = webdriver.ChromeOptions()
# #1允许所有图片；2阻止所有图片；3阻止第三方服务器图片
# prefs = {
#     'profile.default_content_setting_values': {
#         'images': 2
#     }
# }
# options.add_experimental_option('prefs', prefs)


# driver = webdriver.Chrome(chrome_options=options)
driver = webdriver.Chrome()


class ABCC(object):
    driver = webdriver.Chrome()

    def login(self):
        # TODO:不用每次登录 or 直接从手机获取:) 滑动条
        try:
            login_wait = WebDriverWait(driver, 1)
            driver.get(config.ABCC.login_url)

            account_ele = login_wait.until(EC.presence_of_element_located((By.NAME, 'auth_key')))
            account_ele.clear()
            account_ele.send_keys(config.ABCC.account)

            passwd_ele = login_wait.until(EC.presence_of_element_located((By.NAME, 'password')))
            passwd_ele.clear()
            passwd_ele.send_keys(config.ABCC.passwd)

            driver.find_element_by_id('submit').click()
            print('输入二次验证码')
            element = WebDriverWait(driver, 500).until(EC.title_contains("个人中心"))
            return True

        except:
            # TODO:log
            print(util.error_msg())
            return False

    def get_ticker(self):
        """盘口"""
        try:
            wait = WebDriverWait(driver, 30)
            ask_ele = wait.until(EC.presence_of_element_located((
                By.XPATH, '//tbody[@class="scrollStyle ask-table"]/tr[last()]/td[1]')
            ))
            ask_price = decimal.Decimal(ask_ele.text)

            bid_ele = wait.until(EC.presence_of_element_located((
                By.XPATH, '//tbody[@class="scrollStyle bid-table"]/tr[1]/td[1]')
            ))
            bid_price = decimal.Decimal(bid_ele.text)

            return {
                const.SIDE.ASK: ask_price,
                const.SIDE.BID: bid_price,
            }
        except:
            print(util.error_msg())
            raise Exception()

    def get_balance(self):
        import re
        pair = config.ABCC.pair
        ask, bid = pair.upper().split('_')

        try:
            wait = WebDriverWait(driver, 10)
            ele = wait.until(EC.presence_of_all_elements_located((
                By.XPATH, '//div[@class="balance semi-bold"]')
            ))

            pattern = r'(\w+).*?(\d+\.\d*)'
            c = {}
            for e in ele:
                currency_name, amount = re.search(pattern, e.text.strip(), re.S).groups()
                c[currency_name] = decimal.Decimal(amount)

            return {
                const.SIDE.BID: c[bid],
                const.SIDE.ASK: c[ask],
            }
        except:
            print(util.error_msg())
            raise Exception()

    def cancel_all_order(self):
        sleep(2)
        wait = WebDriverWait(driver, 10)
        try:
            # wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div[6]/div[1]/table/thead/tr/th[10]/div/span/span'))).click()
            wait.until(EC.presence_of_element_located((
                By.XPATH, '//span[@class="btn el-popover__reference"]'
            ))).click()
            # wait.until(EC.visibility_of_element_located((By.XPATH, '//button[@class="btn ok"]'))).click()
            wait.until(EC.visibility_of_element_located((
                By.XPATH, '/html[1]/body[1]/div[3]/div[1]/div[2]/button[2]'
            ))).click()
        except:
            print(util.error_msg())
        finally:
            return not self._check_order()

    def _check_order(self):
        sleep(4)
        wait = WebDriverWait(driver, 10)
        order_table_xpath = '//div[@class="bottom-current-delegation"]/table/div/tbody/tr/td'
        order_ele = wait.until(EC.presence_of_all_elements_located((By.XPATH, order_table_xpath)))
        # > 1 有单
        return len(order_ele) > 1

    def get_pending_order(self):

        def _type(td):
            if '限' in td[2].text and '卖' in td[3].text:
                return const.ORDER_TYPE.LIMIT_SELL
            if '限' in td[2].text and '买' in td[3].text:
                return const.ORDER_TYPE.LIMIT_BUY

        wait = WebDriverWait(driver, 10)
        order_table_xpath = '//div[@class="bottom-current-delegation"]/table/div/tbody/tr'
        order_ele = wait.until(EC.presence_of_all_elements_located((By.XPATH, order_table_xpath)))

        pending_orders = []
        for e in order_ele:
            td_ele = e.find_elements_by_tag_name('td')
            pending_orders.append({
                'pair': td_ele[1].text,
                'type': _type(td_ele),
                'price': util.safe_decimal(td_ele[4].text),
                'amount': util.safe_decimal(td_ele[5].text),
                'filled_amount': util.safe_decimal(td_ele[6].text),
                'unsettled_amount': util.safe_decimal(td_ele[7].text),
                'cancel_btn': td_ele[9]
            })
        return pending_orders

    def limit_sell(self, price, amount):
        if amount < self.balance[const.SIDE.ASK] and price * amount > config.ABCC.min_trade:
            ask_form_xpath = '//div[@class="order-submit order-form"]/div[2]'
            price_ele = driver.find_element_by_xpath(
                ask_form_xpath + '/div[@class="input-label input-item input-price"]/input')
            price_ele.clear()
            price_ele.send_keys(str(price))
            amount_ele = driver.find_element_by_xpath(
                ask_form_xpath + '/div[@class="input-label input-item input-amout"]/input')
            amount_ele.clear()
            amount_ele.send_keys(str(amount))
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                (By.XPATH, ask_form_xpath + '/button[@class="btn sell fm"]')
            )).click()
            # submit_ele = driver.find_element_by_xpath(ask_form_xpath + '/button[@class="btn sell fm"]')
            # submit_ele.click()
            log.info('LIMIT_SELL [{price} , {amount} ]  depth[ {ask},{bid} ]'.format(
                price=price, amount=amount, ask=self.ticker[const.SIDE.ASK], bid=self.ticker[const.SIDE.BID]
            ))
            return self._check_order()

    def limit_buy(self, price, amount):
        if self.balance[const.SIDE.BID] > price * amount > config.ABCC.min_trade:
            bid_form_xpath = '//div[@class="order-submit order-form"]/div[1]'
            price_ele = driver.find_element_by_xpath(
                bid_form_xpath + '/div[@class="input-label input-item input-price"]/input')
            price_ele.clear()
            price_ele.send_keys(str(price))
            amount_ele = driver.find_element_by_xpath(
                bid_form_xpath + '/div[@class="input-label input-item input-amout"]/input')
            amount_ele.clear()
            amount_ele.send_keys(str(amount))

            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                (By.XPATH, bid_form_xpath + '/button[@class="btn buy fm"]')
            )).click()

            # submit_ele = driver.find_element_by_xpath(bid_form_xpath + '/button[@class="btn buy fm"]')
            # submit_ele.click()
            log.info('LIMIT_BUY [{price} , {amount} ]  depth[ {ask},{bid} ]'.format(
                price=price, amount=amount, ask=self.ticker[const.SIDE.ASK], bid=self.ticker[const.SIDE.BID]
            ))
            sleep(1)

    def trade(self):
        def _pre():
            try:
                driver.get(config.ABCC.tar_url)
                # 限价单
                limit_order_ele = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@class="th5-tasb tab"]/div[1]')))
                limit_order_ele.click()
                if '限价' in limit_order_ele.find_element_by_tag_name('span').text:
                    sleep(0.3)
                    return True
            except:
                return False

        def _strategy():
            spread = self.ticker[const.SIDE.ASK] - self.ticker[const.SIDE.BID]
            if spread > config.ABCC.price_point:
                # 有空隙
                order_price = round(float(self.ticker[const.SIDE.BID]) + random.uniform(0, float(spread)),
                                    util.get_round(config.ABCC.price_point))

                order_amount = round(
                    random.uniform(float(config.ABCC.amount_point), float(self.balance[const.SIDE.ASK] / 2)),
                    util.get_round(config.ABCC.amount_point))

                is_ok = self.limit_sell(util.safe_decimal(order_price), util.safe_decimal(order_amount))
                if is_ok is None:
                    log.info('no suitable order')
                    return
                if is_ok:
                    pending_order = self.get_pending_order()
                    self.limit_buy(pending_order[0]['price'], pending_order[0]['unsettled_amount'])
                else:
                    log.warn('sell order has filled | may be not enough money')

        is_prepare = _pre()
        if is_prepare:
            while True:
                # TODO: 块价值 or balance check
                is_ok = self.cancel_all_order()
                if is_ok:
                    log.info('CANCEL ALL ORDER')
                    sleep(3)
                    try:
                        self.ticker = self.get_ticker()
                        self.balance = self.get_balance()
                        _strategy()
                    except:
                        log.error(util.error_msg())

    def run(self):
        is_ok = self.login()
        if is_ok:
            self.trade()


if __name__ == '__main__':
    ABCC().run()