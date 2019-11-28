#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/11/27 16:44
"""
import os

try:
    import signal
except ImportError:
    signal =None

try:
    import fcntl
except ImportError:
    if os.name == "nt":
        import win32_support
        import win32_support as fcntl
    else:
        raise


class IOLoop(object):
    """一个水平触发的 I/O 循环

    如果 epoll 可用就使用epoll, 否则就会调用 select()
    如果你正在实现一个1k并发的服务, 可以在linux上编译我们提供的epoll.c模块来获得支持
    """
