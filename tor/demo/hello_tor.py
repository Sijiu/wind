#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/12/10 15:45
"""

import sys
import signal
from wsgiref.simple_server import make_server

import tor.web, tor.ioloop, tornado.wsgi
import tor.httpserver
from tor.options import define, options


define("port", default=8001, help="run on the given port", type=int)


class MainHandler(tor.web.RequestHandler):
    def get(self):
        self.write("Hello, world! Happy, Labour day!")


class IndexHandler(tor.web.RequestHandler):

    def get(self):
        self.write("Hello, Index Page!")


def test_join():

    _all = [u"房子", u"车子", u"孩子", u"票子"]
    cut = True
    if cut:
        print "pain"
        pass
    else:
        # print "-".join(all[:2]), "-".join(all[2:])
        print _all[:2], "or", _all[2:]


def signal_handler(sig, frame):
    print "You pressed Ctrl + C!"
    sys.exit(0)


def start_tor(application):
    print options.port

    http_server = tor.httpserver.HTTPServer(application)

    http_server.listen(options.port)
    tor.ioloop.IOLoop.instance().start()

def start_built_serve(application):
    httpd = make_server("", options.port, application)
    print "WSGIServer: serving HTTP on port %s ...\n" % options.port
    httpd.serve_forever()
    print('Press Ctrl+C')
    signal.pause()
    sys.exit(0)


tornado_app = tor.web.Application([
            (r'/', MainHandler),
            (r'/index', IndexHandler)
        ]
    )

signal.signal(signal.SIGINT, signal_handler)

app = tornado.wsgi.WSGIAdapter(tornado_app)
# app = tor.wsgi.WSGIApplication(tornado_app)


if __name__ == '__main__':

    # start_tor(app)
    start_built_serve(app)

