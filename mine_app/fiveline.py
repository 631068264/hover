#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author = 'wyx'
@time = 2018/8/5 11:30
@annotation = ''
"""
import importme

importme.cli_init()

import json
import time
from datetime import datetime

import click
from appium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from base import util

host = 'localhost'
port = 4723
url = 'http://{host}:{port}/wd/hub'.format(host=host, port=port)
desired_caps = {'deviceName': 'ONEPLUS_A5000', 'appPackage': 'com.kingnet.fiveline',
                'appActivity': 'com.kingnet.fiveline.ui.welcome.WelcomeActivity', 'platformName': 'Android',
                'noReset': True,
                'appWaitActivity': 'com.kingnet.fiveline.ui.main.MainActivity',
                'automationName': 'uiautomator2',
                'resetKeyboard': True,
                'newCommandTimeout': 0,
                }
print(json.dumps(desired_caps))


class FIVE_LINE(object):
    step = 20

    def __init__(self):
        self._create_driver()
        self.wait = WebDriverWait(self.driver, 5)
        self._get_window_size()
        self.read_logs(ignore=True)

    def _get_window_size(self):
        self.width = self.driver.get_window_size()['width']
        self.height = self.driver.get_window_size()['height']

    # def refresh(self):
    #     """下拉刷新"""
    #     x = self.width * 0.5
    #     start_y = self.height * 0.35
    #     end_y = self.height * 0.80
    #     self.driver.swipe(x, start_y, x, end_y)
    def _create_driver(self):
        self.driver = webdriver.Remote(url, desired_capabilities=desired_caps)
        print('driver start')

    def read_logs(self, log_type='logcat', ignore=False):
        raw_logs = self.driver.get_log(log_type)
        if ignore:
            return []

        logs = []
        for raw_log in raw_logs:
            timestamp_sec = raw_log['timestamp'] / 1000
            time_str = datetime.fromtimestamp(timestamp_sec).strftime('%Y-%m-%d %H:%M:%S')
            log = '%s %s' % (time_str, raw_log['message'])
            logs.append(log)

        return logs

    def write_log(self, log_name=None):
        log_name = self.__class__.__name__ + '.log' if log_name is None else log_name
        while True:
            with open(log_name, 'ab') as f:
                logs = self.read_logs()
                lines = [(log + '\n').encode('utf8') for log in logs]
                f.writelines(lines)

    def logcat_output(self):
        import threading
        output = threading.Thread(target=self.write_log)
        output.setDaemon(True)
        output.start()

    def wait_view_id(self, resource_id, wait_sec=None):
        wait = self.wait if wait_sec is None else WebDriverWait(self.driver, wait_sec)
        return wait.until(
            EC.presence_of_element_located((By.ID, resource_id)))

    def wait_views_id(self, resource_id, wait_sec=None):
        wait = self.wait if wait_sec is None else WebDriverWait(self.driver, wait_sec)
        return wait.until(
            EC.presence_of_all_elements_located((By.ID, resource_id)))

    def wait_view_xpath(self, xpath):
        return self.wait.until(
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

    def swipe_down(self):
        """下滑文章页面"""
        x = self.width * 0.5
        start_y = self.height * 0.8
        end_y = self.height * 0.6
        before_page = self.driver.page_source
        self.driver.swipe(x, start_y, x, end_y)
        after_page = self.driver.page_source
        return before_page != after_page

    def swipe_up(self):
        """上滑"""
        x = self.width * 0.5
        start_y = self.height * 0.6
        end_y = self.height * 0.8
        before_page = self.driver.page_source
        self.driver.swipe(x, start_y, x, end_y)
        after_page = self.driver.page_source
        return before_page != after_page

    def send_comment(self, text):
        """评论"""
        input = self.wait_view_id('com.kingnet.fiveline:id/mTextCommentAction')
        input.click()
        try:
            comment = self.wait_view_id('com.kingnet.fiveline:id/mEditCommentInput')
            comment.send_keys(text)
            send = self.wait_view_id('com.kingnet.fiveline:id/mTextCommentAction')
            send.click()
            # 反手一个赞
            like = self.wait_view_id('com.kingnet.fiveline:id/mBtnLike')
            like.click()
        except:
            # 评论功能关闭
            pass

    def to_share(self):
        """分享"""
        share = self.wait_view_id('com.kingnet.fiveline:id/ivShare')
        share.click()
        wechat = self.wait_view_id('com.kingnet.fiveline:id/ivMoreWechat')
        wechat.click()

        share_list = self.wait_views_id('com.tencent.mm:id/om')
        for s in share_list:
            if s.text == '文件传输助手':
                s.click()
                wechat_share = self.wait_view_id('com.tencent.mm:id/au_')
                wechat_share.click()
                time.sleep(0.6)
                wechat_back = self.wait_view_id('com.tencent.mm:id/au9')
                wechat_back.click()
                return

    def to_praise(self):
        """点赞"""

        while self.swipe_up():
            time.sleep(2)
            praise = self.try_view_id('com.kingnet.fiveline:id/mLayoutOperatePraise')
            be_praised = self.try_view_id('com.kingnet.fiveline:id/tvCostType')
            if praise:
                praise.click()
                return
            elif be_praised:
                return

    def get_comment(self):
        filter_keyword = ['五条', '赞', '矿', '6', '互', '邀请码']
        while True:
            extend_eles = self.try_views_id('com.kingnet.fiveline:id/expandable_text')
            if extend_eles:
                for comment in extend_eles:
                    if all(k not in comment.text for k in filter_keyword) and len(comment.text) > 4:
                        return comment.text
            flag = self.swipe_down()
            if not flag:
                return self.title + '给力啊 ☆(￣▽￣)/'

    def refresh(self):
        index_view = self.wait_view_id('com.kingnet.fiveline:id/flMainHome')
        index_view.click()

    def back(self):
        back_view = self.wait_view_id('com.kingnet.fiveline:id/mImageHomePageBack')
        back_view.click()

    def do_task(self, view):
        # 进入文章
        view.click()
        time.sleep(0.6)
        self.title = self.wait_view_id('com.kingnet.fiveline:id/mTextConsultTitle').text
        self.send_comment('给我赞')
        self.to_praise()
        text = self.get_comment()
        if text:
            self.send_comment(text + ' 求赞')
            self.to_share()

        self.back()
        self.refresh()

    def harvest(self):
        import re
        wallet = self.wait_view_id('com.kingnet.fiveline:id/flMainWallet')
        wallet.click()

        while self.swipe_up():
            pass

        profit = self.wait_view_id('com.kingnet.fiveline:id/gv_detail_profit')
        profit.click()

        while self.swipe_down():
            views = self.try_views_id('com.kingnet.fiveline:id/tvFunction')
            if views and len(views) == 4:
                break

        flag = False
        for v in views:
            task_num, max_num = re.search(r'(\d+) / (\d+)', v.text).groups()
            # flag == True 未完成任务
            flag |= (task_num != max_num)
            if flag:
                break

        index_view = self.wait_view_id('com.kingnet.fiveline:id/flMainHome')
        index_view.click()

        return flag

    def close(self):
        self.driver.close_app()

    def discover(self, del_mark=False):

        def _mark():
            self.wait_view_id('com.kingnet.fiveline:id/mLayoutMark').click()

        def _back():
            self.driver.find_element_by_accessibility_id('Navigate up').click()

        def _next():
            self.wait_view_id('com.kingnet.fiveline:id/mLayoutNext').click()

        def _is_video_type():
            video = self.try_view_id('com.kingnet.fiveline:id/tXCloudVideoView')
            if video:
                return True

        def _vote():
            vote = self.wait_view_id('com.kingnet.fiveline:id/voteBtn')
            if vote:
                vote.click()
                return True
            return False

        def _clear_mark():

            self.wait_view_id('com.kingnet.fiveline:id/tvHeadRight').click()
            self.wait_view_id('com.kingnet.fiveline:id/cbSelectAll').click()

            self.wait_view_id('com.kingnet.fiveline:id/llFinderDelete').click()

        def _is_del_clear():
            time.sleep(0.3)
            return self.try_view_id('com.kingnet.fiveline:id/clFinder')

        def _is_finished():
            vote_num = self.wait_view_id('com.kingnet.fiveline:id/tvVoteValueNum').text
            vote_max_num = self.wait_view_id('com.kingnet.fiveline:id/tvVoteMax').text
            return vote_num == vote_max_num

        if not del_mark:
            try:
                self.wait_view_id('com.kingnet.fiveline:id/flMainFound').click()
                if _is_finished():
                    self.close()
                    return
                self.wait_view_id('com.kingnet.fiveline:id/flFindContent').click()
                for i in range(self.step * 2):
                    if i > 1 and i % 10 == 0:
                        raise WebDriverException
                    if _is_video_type():
                        _mark()
                    else:
                        while self.swipe_down():
                            time.sleep(0.6)
                            if _vote():
                                break

                    _next()

                self.close()
            except WebDriverException:
                print(util.error_msg())
                self._create_driver()
                self.discover(del_mark)
        else:
            self.wait_view_id('com.kingnet.fiveline:id/flMainFound').click()
            flag = True
            while flag:
                self.wait_view_id('com.kingnet.fiveline:id/clMarked').click()
                if _is_del_clear():
                    _clear_mark()
                    _back()
                else:
                    flag = False

    def task(self):
        try:
            for i in range(self.step):
                if not self.harvest():
                    self.close()
                    return
                content_view_list = self.wait_views_id('com.kingnet.fiveline:id/lsecTitle')
                self.do_task(content_view_list[1])
                raise WebDriverException

        except WebDriverException:
            print(util.error_msg())
            self._create_driver()
            self.task()

    def run(self):
        # self.logcat_output()
        # self.task()
        # self.discover(del_mark=True)
        self.discover(del_mark=False)
        self.driver.close_app()

    def __del__(self):
        self.driver.close_app()


@click.group()
def cli():
    pass


@cli.command()
def discover():
    f = FIVE_LINE()
    f.discover(del_mark=False)
    f.driver.close_app()


@cli.command()
def del_mark():
    f = FIVE_LINE()
    f.discover(del_mark=True)
    f.driver.close_app()


@cli.command()
def task():
    f = FIVE_LINE()
    f.task()
    f.driver.close_app()


if __name__ == '__main__':
    cli()
