#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author = 'wyx'
@time = 2018/8/7 14:34
@annotation = ''
"""

import decimal
import random
import re
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from base import config, logger, util, const
from base.stash import Stash
from google_auth import android_auth_code

conf = config.ABCC
logger.AutoLog.log_path = 'logs'
strategy_id = 'abcc_{}'.format(conf.pair.lower())
log = logger.AutoLog.file_log(strategy_id)


# options = webdriver.ChromeOptions()
# #1允许所有图片；2阻止所有图片；3阻止第三方服务器图片
# prefs = {
#     'profile.default_content_setting_values': {
#         'images': 2
#     }
# }
# options.add_experimental_option('prefs', prefs)
# driver = webdriver.Chrome(chrome_options=options)
class STRATEGY_FLAG(object):
    FLAG_SB = 'FLAG_SB'
    FLAG_BS = 'FLAG_BS'


class MODE(object):
    FLAG_SB = 'FLAG_SB'
    FLAG_BS = 'FLAG_BS'

    FILL_S = 'FILL_S'
    FILL_B = 'FILL_B'

    NAME_DICT = {
        FLAG_SB: STRATEGY_FLAG.FLAG_SB,
        FLAG_BS: STRATEGY_FLAG.FLAG_BS,

        FILL_S: STRATEGY_FLAG.FLAG_BS,
        FILL_B: STRATEGY_FLAG.FLAG_SB,
    }


MODE_KEY = 'mode'
BALANCE_KEY = 'balance'
driver = webdriver.Chrome()


class ABCC(object):

    def __init__(self):
        # 中文
        driver.get(conf.login_url)
        driver.add_cookie({
            'name': 'lang',
            'value': 'zh-CN',
        })

        self.min_trade = conf.min_trade
        self.price_point = util.point2decfloat(conf.price_point)
        self.amount_point = util.point2decfloat(conf.amount_point)
        self.balance_percent = conf.balance_percent

    def _dialog_close(self):
        wait = WebDriverWait(driver, 5)
        try:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'dialog-content')))
        except:
            return
        driver.find_element_by_css_selector('.iconfont.icon-guanbi').click()

    def login(self):
        try:
            wait = WebDriverWait(driver, 500)
            driver.get(conf.login_url)

            self._dialog_close()

            account_ele = wait.until(EC.presence_of_element_located((By.NAME, 'auth_key')))
            account_ele.clear()
            account_ele.send_keys(conf.account)

            passwd_ele = wait.until(EC.presence_of_element_located((By.NAME, 'password')))
            passwd_ele.clear()
            passwd_ele.send_keys(conf.passwd)

            driver.find_element_by_id('submit').click()

            print('输入二次验证码')
            if conf.auto_auth:
                auth_input = wait.until(EC.presence_of_element_located((
                    By.XPATH, '//div[@class="google-input"]/div/input'
                )))
                flag = True
                while flag:
                    code = android_auth_code(conf.device_name, conf.auth_key)
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

    def get_ticker(self):
        """盘口"""
        try:
            wait = WebDriverWait(driver, 30)
            ask_ele = wait.until(EC.presence_of_element_located((
                By.XPATH, '//tbody[@class="scrollStyle ask-table"]/tr[last()]/td[1]')
            ))
            ask_price = util.safe_decimal(ask_ele.text)

            bid_ele = wait.until(EC.presence_of_element_located((
                By.XPATH, '//tbody[@class="scrollStyle bid-table"]/tr[1]/td[1]')
            ))
            bid_price = util.safe_decimal(bid_ele.text)

            return {
                const.SIDE.ASK: ask_price,
                const.SIDE.BID: bid_price,
            }
        except:
            log.error(util.error_msg())
            raise Exception('Error ticker')

    def get_balance(self):
        pair = conf.pair
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
            log.error(util.error_msg())
            raise Exception('Error balance')

    def update_market(self):
        self.ticker = self.get_ticker()
        self.balance = self.get_balance()

    def cancel_all_order(self):
        sleep(2)
        wait = WebDriverWait(driver, 10)
        order_table_xpath = '//div[@class="bottom-current-delegation"]/table/div/tbody/tr'
        try:
            order_ele = wait.until(EC.presence_of_all_elements_located((By.XPATH, order_table_xpath)))
            for e in order_ele:
                td_ele = e.find_elements_by_tag_name('td')
                if td_ele and len(td_ele) > 1:
                    td_ele[9].click()
                    sleep(0.5)
                    wait.until(EC.presence_of_element_located((
                        By.XPATH, '/html[1]/body[1]/div[3]/div[1]/div[2]/button[2]'
                    ))).click()
        except:
            log.error(util.error_msg())
        finally:
            return not self._check_order()

    def _check_order(self):
        sleep(3)
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

    def limit_sell(self, price, amount=None, volume=None):
        ask_form_xpath = '//div[@class="order-submit order-form"]/div[2]'
        price_ele = driver.find_element_by_xpath(
            ask_form_xpath + '/div[@class="input-label input-item input-price"]/input')
        price_ele.clear()
        price_ele.send_keys(str(price))

        if amount and amount < self.balance[const.SIDE.ASK] and price * amount > self.min_trade:
            amount_ele = driver.find_element_by_xpath(
                ask_form_xpath + '/div[@class="input-label input-item input-amout"]/input')
            amount_ele.clear()
            amount_ele.send_keys(str(amount))
        elif volume and volume / price < self.balance[const.SIDE.ASK] and volume > self.min_trade:
            volume_ele = driver.find_element_by_xpath(
                ask_form_xpath + '/div[@class="input-label input-item input-total"]/input')
            volume_ele.clear()
            volume_ele.send_keys(str(volume))
        else:
            return

        sleep(0.3)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.XPATH, ask_form_xpath + '/button[@class="btn sell fm"]')
        )).click()

        log.info('LIMIT_SELL [ {price} , {amount} ]  depth[ {bid}< {price} <{ask} ]'.format(
            price=price, amount=amount if amount else volume / price, ask=self.ticker[const.SIDE.ASK],
            bid=self.ticker[const.SIDE.BID]
        ))
        return self._check_order()

    def limit_buy(self, price, amount=None, volume=None):
        bid_form_xpath = '//div[@class="order-submit order-form"]/div[1]'
        price_ele = driver.find_element_by_xpath(
            bid_form_xpath + '/div[@class="input-label input-item input-price"]/input')
        price_ele.clear()
        price_ele.send_keys(str(price))

        if amount and self.balance[const.SIDE.BID] > price * amount > self.min_trade:
            amount_ele = driver.find_element_by_xpath(
                bid_form_xpath + '/div[@class="input-label input-item input-amout"]/input')
            amount_ele.clear()
            amount_ele.send_keys(str(amount))
        elif volume and self.balance[const.SIDE.BID] > volume > self.min_trade:
            volume_ele = driver.find_element_by_xpath(
                bid_form_xpath + '/div[@class="input-label input-item input-total"]/input')
            volume_ele.clear()
            volume_ele.send_keys(str(volume))
        else:
            return

        sleep(0.3)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.XPATH, bid_form_xpath + '/button[@class="btn buy fm"]')
        )).click()

        log.info('LIMIT_BUY [ {price} , {amount} ]  depth[ {bid}< {price} <{ask}]'.format(
            price=price, amount=amount if amount else volume / price, ask=self.ticker[const.SIDE.ASK],
            bid=self.ticker[const.SIDE.BID]
        ))
        return self._check_order()

    def _judge_mode(self, stash):
        mode = stash.get(MODE_KEY)
        if mode is None:
            return STRATEGY_FLAG.FLAG_SB
        return MODE.NAME_DICT[mode]

    def _dry_try_volume(self, side):
        # TODO:fix limit_buy or limit_sell xpath
        pattern = r'.*(\d+\.\d*).*'
        ask_form_xpath = '//div[@class="order-submit order-form"]/div[2]'
        price_ele = driver.find_element_by_xpath(
            ask_form_xpath + '/div[@class="input-label input-item input-price"]/input')
        price_ele.clear()
        price_ele.send_keys(str(self.ticker[const.SIDE.BID]))
        amount_ele = driver.find_element_by_xpath(
            ask_form_xpath + '/div[@class="input-label input-item input-amout"]/input')
        ask_amount = util.safe_decimal(re.search(pattern, amount_ele.get_attribute('placeholder')).groups()[0])
        ask_volume = self.ticker[const.SIDE.BID] * ask_amount
        bid_volume = self.balance[const.SIDE.BID]
        volume = (ask_volume + bid_volume) / 2
        if side == const.SIDE.ASK:
            return bid_volume - volume
        return ask_volume - volume

    def _balance_asset(self, price, stash):
        """平衡资产"""

        def _flag_min_trade(side):
            if side == const.SIDE.BID:
                return self._get_amount_balance(side) <= self.min_trade
            else:
                return price * self._get_amount_balance(side) <= util.deal_min_trade(self.min_trade)

        side = stash.get(BALANCE_KEY, None)
        if side:
            self.balance = self.get_balance()
            if _flag_min_trade(side):
                log.warn('not enough money to {}'.format(side).lower())
                self.ticker = self.get_ticker()
                if (self.ticker[const.SIDE.ASK] / self.ticker[const.SIDE.BID]) - 1 * 100 < self.balance_percent:
                    balance_volume = self._dry_try_volume(side)
                    is_pending = True
                    if side == const.SIDE.ASK:
                        # 卖不够钱 买入
                        is_pending = self.limit_buy(self.ticker[side], volume=balance_volume)
                    elif side == const.SIDE.BID:
                        # 买不够钱 卖出
                        is_pending = self.limit_sell(self.ticker[side], volume=balance_volume)

                    if is_pending:
                        # 未完全平衡
                        self.cancel_all_order()
                        self._balance_asset(price, stash)

                    log.info('BALANCED_ASSET SUCCESS {}'.format(side))
                    del stash[BALANCE_KEY]
                    self.update_market()
                    return
                log.warn('BALANCED_ASSET FAILED Depth spread too large {:.4%} > {:.4%}'.format(
                    self.ticker[const.SIDE.ASK] / self.ticker[const.SIDE.BID] - 1, self.balance_percent / 100))
                return

            del stash[BALANCE_KEY]
            self.update_market()

    def _get_amount_balance(self, side):
        """刷量头寸控制"""
        return self.balance[side] / 2

    def trade(self):

        def _pre():
            try:
                driver.get(conf.tar_url)
                # 限价单
                limit_order_ele = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@class="th5-tasb tab"]/div[1]')))
                limit_order_ele.click()
                flag1 = '限价' in limit_order_ele.find_element_by_tag_name('span').text

                # 隐藏其他不相关交易对
                hid_pair_ele = driver.find_element_by_xpath(
                    '/html/body/div[2]/div[6]/div[1]/div/div/label/span[1]/span')
                hid_pair_ele.click()

                hid_pair_ele = driver.find_element_by_xpath(
                    '/html/body/div[2]/div[6]/div[2]/div/div/label/span[1]/span')
                hid_pair_ele.click()
                sleep(0.3)
                return flag1
            except:
                log.error(util.error_msg())
                return False

        def _strategy():
            """
            瞄准买一卖一缝隙刷单 目标是尽量成交自己的单,持续时间尽量久

            先卖后买 先买后卖     两种操作 交替执行
            sell_buy buy_sell


            单被吃 反向操作进行两次
            Example:
                进行buy_sell 导致买单被吃  之后做两次sell_buy 再buy_sell sell_buy 循环

            保存操作状态

            :return:
            """
            spread = self.ticker[const.SIDE.ASK] - self.ticker[const.SIDE.BID]
            order_price = util.safe_decimal(round(
                float(self.ticker[const.SIDE.BID]) +
                random.uniform(float(self.price_point), float(spread - self.price_point)),
                util.get_round(self.price_point)))

            order_amount = util.safe_decimal(round(
                random.uniform(float(self.amount_point), float(self._get_amount_balance(const.SIDE.ASK))),
                util.get_round(self.amount_point)))

            with Stash(strategy_id) as stash:
                self._balance_asset(order_price, stash)
                if spread > self.price_point:
                    # 有空隙
                    if self._judge_mode(stash) == STRATEGY_FLAG.FLAG_SB:
                        is_ok = self.limit_sell(order_price, order_amount)
                        if is_ok is None:
                            stash[MODE_KEY] = MODE.FLAG_BS
                            stash[BALANCE_KEY] = const.SIDE.ASK
                            log.info('no suitable sell order')
                            return

                        if is_ok:
                            pending_order = self.get_pending_order()
                            self.limit_buy(pending_order[0]['price'], pending_order[0]['unsettled_amount'])

                            if stash.get(MODE_KEY) == MODE.FILL_B:
                                stash[MODE_KEY] = MODE.FLAG_SB
                            else:
                                stash[MODE_KEY] = MODE.FLAG_BS
                        else:
                            log.warn('sell order has filled')
                            stash[MODE_KEY] = MODE.FILL_S
                    else:
                        is_ok = self.limit_buy(order_price, order_amount)
                        if is_ok is None:
                            stash[MODE_KEY] = MODE.FLAG_SB
                            stash[BALANCE_KEY] = const.SIDE.BID
                            log.info('no suitable buy order')
                            return
                        if is_ok:
                            pending_order = self.get_pending_order()
                            self.limit_sell(pending_order[0]['price'], pending_order[0]['unsettled_amount'])

                            if stash.get(MODE_KEY) == MODE.FILL_S:
                                stash[MODE_KEY] = MODE.FLAG_BS
                            else:
                                stash[MODE_KEY] = MODE.FLAG_SB
                        else:
                            log.warn('buy order has filled')
                            stash[MODE_KEY] = MODE.FILL_B
                else:
                    wait_spread = random.uniform(1, 10)
                    msg = 'BID ASk price too close sleep {} sec'.format(wait_spread)
                    log.info(msg)
                    print(msg)
                    sleep(wait_spread)

        is_prepare = _pre()
        if is_prepare:
            while True:
                # TODO: 块价值 or balance check
                is_ok = self.cancel_all_order()
                if is_ok:
                    log.info('CANCEL ALL ORDER')
                    sleep(2)
                    try:
                        self.update_market()
                        _strategy()
                    except:
                        log.error(util.error_msg())

    def run(self):
        is_ok = self.login()
        if is_ok:
            self.trade()


if __name__ == '__main__':
    ABCC().run()
