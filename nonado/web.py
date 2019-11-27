#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/11/27 16:21
"""
import httplib


class RequestHandler(object):
    """
    本类的子类 应该定义一个有 get() 或者post() 方法的handler.

    如果想支持更多的方法, 可以在自己的 RequestHandler 类中重写 SUPPORTED_METHODS 类变量
    """

    supported_methods= ("GET", "HEAD", "POST", "DELETE", "PUT")

    def __init__(self, application, request, transforms=None):
        self.application = application
        self.request = request
        self._headers_written = False
        self._finished = False
        self._auto_finish = True
        self._transforms = transforms or []
        # self.ui = _O(("..."))
        # self.ui["modules"] = _O(("..."))
        self.clear()
        # 检查 WSGI 初始 connection 是否可用 Web服务器网关接口（Python Web Server Gateway Interface，缩写为WSGI）
        if hasattr(self.request, "connection"):
            self.request.connection.stream.set_close_callback(self.on_connection_close)

        def get(self, *args, **kwargs):
            raise HTTPError(405)


class HTTPError(Exception):
    """An exception that will turn into an HTTP error response."""
    def __init__(self, status_code, log_message=None, *args):
        self.status_code = status_code
        self.log_message = log_message
        self.args = args

    def __str__(self):
        message = "HTTP %d: %s" % (
            self.status_code, httplib.responses[self.status_code])
        if self.log_message:
            return message + " (" + (self.log_message % self.args) + ")"
        else:
            return message