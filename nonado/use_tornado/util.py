#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/12/4 14:45
"""

import tornado.ioloop


COUNTER = 0


def stop_loop(times):
    global COUNTER
    COUNTER += 1
    if COUNTER == times:
        tornado.ioloop.IOLoop.instance().stop()
        print "====> ioloop end"


def start_loop():
    print "====> ioloop start"
    ioloop = tornado.ioloop.IOLoop.current()
    ioloop.start()