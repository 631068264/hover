#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author = 'wyx'
@time = 2018/9/29 21:21
@annotation = ''
"""
import numpy as np

keep_prob = 0.8

a = np.random.rand(2, 2)
b = np.random.rand(a.shape[0], a.shape[1]) < keep_prob
c = a * b
c /= keep_prob
print(c)

# # d = np.multiply(a, b)
# # print(d)
#
# e = c / keep_prob
#
# print(e)
