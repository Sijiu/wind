#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: plain
@time:2019/12/1 下午11:13
"""

from __future__ import unicode_literals


class TestMiddle(object):

    def __init__(self, application):
        self.application = application

    def __call__(self, *args, **kwargs):
        print args
        print kwargs
        environ, start_response = args
        # if 'postman' in environ.get("USER_AGENT"):
        if 'postman' in environ.get("USER_AGENT") or "curl" in environ.get("USER_AGENT"):
            start_response("403, Not Allowed!", [])
            return ["not allowed"]
        return self.application(environ, start_response)
