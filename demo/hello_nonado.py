#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/11/28 14:36
"""


import nonado.web, nonado.ioloop
import nonado.httpserver
from nonado.options import define, options


define("port", default=8001, help="run on the given port", type=int)


class MainHandler(nonado.web.RequestHandler):
    def get(self):
        self.write("Hello, world! Happy, Labour day!")


class IndexHandler(nonado.web.RequestHandler):

    def get(self):
        self.write("Hello, Index Page!")


def main():
    print options.port
    application = nonado.web.Application([
            (r'/', MainHandler),
            (r'/index', IndexHandler)
        ]
    )

    http_server = nonado.httpserver.HTTPServer(application)

    http_server.listen(options.port)
    nonado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    # main()

    # all = [u"房子", u"车子", u"孩子", u"票子"]
    # cut = True
    # if cut:
    #     print "pain"
    #     pass
    # else:
    #     # print "-".join(all[:2]), "-".join(all[2:])
    #     print all[:2], "or", all[2:]
    main()
