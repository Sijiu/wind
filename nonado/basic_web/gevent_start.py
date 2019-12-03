#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/12/3 11:36
"""
import urllib2

from gevent import monkey; monkey.patch_socket()
import gevent


def fn(n):
    for i in range(n):
        print gevent.getcurrent(), i
        gevent.sleep(0) # greenlet 会交替运行, 在此替代有延迟的IO操作

def test_fn():
    g1 = gevent.spawn(fn, 5)
    g2 = gevent.spawn(fn, 5)
    g3 = gevent.spawn(fn, 5)
    g1.join()
    g2.join()
    g3.join()

def get_url(url):
    print 'GET %s ' % url
    resp = urllib2.urlopen(url)
    data = resp.read()
    print  "%s bytes received from %s " % (len(data), url)

gevent.joinall([
    gevent.spawn(get_url, 'https://www.python.org'),
    gevent.spawn(get_url, 'https://www.baidu.com'),
    gevent.spawn(get_url, 'https://www.github.com')
])