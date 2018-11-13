#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author = 'wyx'
@time = 2018/9/12 11:28
@annotation = ''
"""


def cli_init():
    import os

    project_home = os.path.realpath(__file__)
    project_home = os.path.split(project_home)[0]
    import sys

    sys.path.append(os.path.split(project_home)[0])
    sys.path.append(project_home)
    from base import logger
    logger.AutoLog.log_path = 'logs'
