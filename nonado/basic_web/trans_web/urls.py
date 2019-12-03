#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/12/3 17:29
"""

from transwarp import get, view


@view('index.html')
@get("/")
def test_index():
    return dict(name="airport", socore=9.7, time="20191203")