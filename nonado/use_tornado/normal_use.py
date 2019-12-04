#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/12/4 14:55
"""

from tornado.httpclient import  AsyncHTTPClient
from tornado.concurrent import Future
from tornado import gen, ioloop


from util import stop_loop, start_loop


# fetch 返回 future
def async_fetch_future(url):
    http_client = AsyncHTTPClient()
    return http_client.fetch(url)


def async_fetch_future_callback(future):
    result = future.result()
    print "  future_callback"
    print result.request.url, result.code, result.reason, result.request_time
    stop_loop(1)


@gen.coroutine
def divide(x, y):
    return x/ y


def normal_use():
    """必须手动启动 ioloop 并在调用结束之后手动销毁 ioloop，想要获得调用结果必须为 Future 添加回调。

    """
    result_future = async_fetch_future("http://www.apple.com/cn/")
    result_future.add_done_callback(async_fetch_future_callback)
    start_loop()


def not_care__result():
    ioloop.IOLoop.current().spawn_callback(divide, 0, 1)
    ioloop.IOLoop.current().add_timeout(
        ioloop.time.time() + 1, stop_loop, 1
    )
    start_loop()


def init_tag():
    pass

def run_once():
    pass


if __name__ == '__main__':
    # normal_use()
    not_care__result()