#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/12/4 9:51
"""

from tornado import wsgi, httpserver, ioloop
import sys
import signal


def signal_handle(sig, frame):
    print "sig=%s ,  frame=%s " % (sig, frame)
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handle)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit( "请提供一个形如 module:app 的应用程序")
    app_path = sys.argv[0]
    module, app = sys.argv[1].split(":")
    module = __import__(module)
    application = getattr(module, app)

    container = wsgi.WSGIContainer(application)
    http_server = httpserver.HTTPServer(container)
    http_server.listen(8888, "")
    ioloop.IOLoop.instance().start()

    print('Press Ctrl+C')
    signal.pause()
    sys.exit(0)