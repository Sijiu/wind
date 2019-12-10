#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/12/2 17:45
"""
import sys
import signal

from wsgiref.simple_server import make_server

SERVER_ADDRESS = (HOST, PORT) = "", 8888


def signal_handler(sig, frame):
    print "You pressed Ctrl + C!"
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)



if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit("请提供一个形如 module:callable 的应用对象")
    app_path = sys.argv[1]
    module, application = app_path.split(":")
    module = __import__(module)
    application = getattr(module, application)
    httpd = make_server(HOST, PORT, application)
    print "WSGIServer: serving HTTP on port %s ...\n" % PORT
    httpd.serve_forever()
    print('Press Ctrl+C')
    signal.pause()
    sys.exit(0)