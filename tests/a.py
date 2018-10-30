#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author = 'wyx'
@time = 2018/9/18 15:21
@annotation = ''
"""
import base64
from io import BytesIO

from PIL import Image


def img2base64(image_path, img_out=False, css_out=False):
    img = Image.open(image_path)
    output_buffer = BytesIO()
    img.save(output_buffer, format='JPEG')
    byte_data = output_buffer.getvalue()
    base64_str = base64.b64encode(byte_data).decode()

    if img_out:
        return 'data:image/jpeg;base64,{}'.format(base64_str)
    if css_out:
        return 'url("data:image/jpeg;base64,{}")'.format(base64_str)
    return base64_str


def base64_to_img(base64_str, image_path='b.jpeg'):
    import re
    base64_data = re.search('.*?data:image/.*;base64,(.*=)', base64_str).group(1)
    byte_data = base64.b64decode(base64_data)
    img = Image.open(BytesIO(byte_data))
    if image_path:
        img.save(image_path)
    return img


print(img2base64('a.jpg', img_out=False, css_out=True))
