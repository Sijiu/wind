#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/11/30 19:05
"""


import tornado.web, tornado.ioloop
import tornado.httpserver
from tornado.options import define, options


define("port", default=8001, help="run on the given port", type=int)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world! Happy, Labour day!")


class IndexHandler(tornado.web.RequestHandler):

    def get(self):
        self.write("Hello, Index Page!")


def main(application):
    print options.port

    http_server = tornado.httpserver.HTTPServer(application)

    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

app = tornado.web.Application([
            (r'/', MainHandler),
            (r'/index', IndexHandler)
        ]
    )


# if __name__ == '__main__':
#     # main()
#
#     # all = [u"房子", u"车子", u"孩子", u"票子"]
#     # cut = True
#     # if cut:
#     #     print "pain"
#     #     pass
#     # else:
#     #     # print "-".join(all[:2]), "-".join(all[2:])
#     #     print all[:2], "or", all[2:]
#     main(app)
