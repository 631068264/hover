#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author = 'wyx'
@time = 2018/11/12 11:39
@annotation = ''
"""

import importme

importme.cli_init()
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from base import logger, config, util
import json
import random
import time
import re

URL_FORMAT = 'https://www.52pojie.cn/thread-818719-{}-1.html'
URL = URL_FORMAT.format(1)

conf = config.PoJie52
log_name = '52pojie_{}'.format(os.path.basename(__file__).replace('.py', ''))
log = logger.AutoLog.file_log(log_name)
cookie_path = 'login.json'


class RobotMix(object):

    def __init__(self, driver, wait_sec=5):
        self.driver = driver()
        self.wait = WebDriverWait(self.driver, wait_sec)

    def wait_view_id(self, resource_id, wait_sec=None, is_eles=False):
        wait = self.wait if wait_sec is None else WebDriverWait(self.driver, wait_sec)
        if is_eles:
            return wait.until(
                EC.presence_of_all_elements_located((By.ID, resource_id)))
        return wait.until(
            EC.presence_of_element_located((By.ID, resource_id)))

    def wait_view_xpath(self, xpath, wait_sec=None, is_eles=False):
        wait = self.wait if wait_sec is None else WebDriverWait(self.driver, wait_sec)
        if is_eles:
            return wait.until(
                EC.presence_of_all_elements_located((By.XPATH, xpath)))
        return wait.until(
            EC.presence_of_element_located((By.XPATH, xpath)))

    def try_view_id(self, resource_id):
        try:
            view = self.driver.find_element_by_id(resource_id)
        except:
            return None
        return view

    def try_views_id(self, resource_id):
        try:
            view = self.driver.find_elements_by_id(resource_id)
        except:
            return None
        return view

    def try_view_xpath(self, xpath):
        try:
            view = self.driver.find_element_by_xpath(xpath)
        except:
            return None
        return view

    def try_views_xpath(self, xpath):
        try:
            view = self.driver.find_elements_by_xpath(xpath)
        except:
            return None
        return view


class NewBie(RobotMix):
    def __init__(self):
        super().__init__(webdriver.Chrome, 5)
        self.page = 0

    def login(self):
        self.driver.get(URL)
        try:
            username_ele = self.wait_view_id('ls_username')
            username_ele.clear()
            username_ele.send_keys(conf.username)

            passwd_ele = self.wait_view_id('ls_password')
            passwd_ele.clear()
            passwd_ele.send_keys(conf.passwd)

            auto_login = self.try_view_id('ls_cookietime')
            auto_login.click()

            submit = self.wait_view_xpath("//td[@class='fastlg_l']/button[@type='submit']")
            submit.click()

            print('输入验证码')
            flag = True
            while flag:
                try:
                    self.wait.until(EC.visibility_of_element_located((By.ID, 'nc-float')), 1)
                except:
                    flag = False
            print('验证码success')

            cookies = self.driver.get_cookies()
            with open(cookie_path, 'w') as f:
                json.dump(cookies, f)
            try:
                self.wait_view_xpath("//strong[@class='vwmy']")
            except:
                return False
            return True
        except:
            log.error(util.error_msg())
            return False

    def relogin(self):
        with open(cookie_path, 'r') as f:
            cookies = json.load(f)

        try:
            self.driver.get(URL)
            for c in cookies:
                self.driver.add_cookie(c)
            self.driver.refresh()
            try:
                self.wait_view_xpath("//strong[@class='vwmy']", 500)
            except:
                log.error('relogin failed')
                return False
            log.error('relogin success')
            return True
        except:
            log.error(util.error_msg())
            return False

    def get_comment(self):
        filter_keyword = ['href=', 'src=', '2018', ':']
        # total_page = self.wait_view_xpath('//label/span', 10).text
        total_page = self.wait_view_xpath('//label/span').text
        total_page = re.search(r'(\d+)', total_page).groups()[0]
        total_page = int(total_page)
        if self.page == total_page:
            log.info('no new page')
            return None

        self.page = total_page
        page = random.randint(2, total_page - 1)
        self.driver.get(URL_FORMAT.format(page))
        comments_ele = self.wait_view_xpath('//td[@class="t_f"]', is_eles=True)
        for c in comments_ele:
            comment = c.text
            if len(comment) > 6 and all(k not in comment for k in filter_keyword):
                return comment.strip()
        log.info('no suitable page')
        return None

    def send_comment(self, comment):
        msg_ele = self.wait_view_xpath('//textarea[@name="message"]')
        msg_ele.clear()
        msg_ele.send_keys(comment)

        answer_ele = self.try_view_id('secqaaverify_qS0')
        if answer_ele:
            answer_ele.clear()
            answer_ele.click()
            code_ele = self.wait_view_id('seccodeqS0_menu')
            answer = code_ele.text.split('答案：')[1]
            answer_ele.send_keys(answer)
            msg_ele.click()

        auto_last_page = self.try_view_id('fastpostrefresh')
        auto_last_page.click()

        submit = self.wait_view_id('fastpostsubmit')
        submit.click()
        log.info('send {}'.format(comment))

    def run(self):
        wait_rate = 60
        is_ok = self.relogin()
        if not is_ok:
            self.login()
        while True:
            comment = self.get_comment()
            if comment:
                self.send_comment(comment)
            wait_floor = 1 * wait_rate
            wait_ceil = 4 * wait_rate
            sec = random.randint(wait_floor, wait_ceil)
            log.info('sleep {} sec'.format(sec))
            time.sleep(sec)


if __name__ == '__main__':
    robot = NewBie()
    robot.run()
