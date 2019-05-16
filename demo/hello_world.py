#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/5/1 12:00
"""

import mornado.web, mornado.ioloop
import mornado.httpserver
from mornado.options import define, options


define("port", default=8888, help="run on the given port", type=int)


class MainHandler(mornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world! Happy, Labour day!")


class IndexHandler(mornado.web.RequestHandler):

    def get(self):
        self.write("Hello, Index Page!")


def main():
    print options.port
    application = mornado.web.Application([
            (r'/', MainHandler),
            (r'/index', IndexHandler)
        ]
    )

    http_server = mornado.httpserver.HTTPServer(application)

    http_server.listen(options.port)
    mornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    # main()

    all = [u"房子", u"车子", u"孩子", u"票子"]
    cut = True
    if cut:
        print "pain"
        pass
    else:
        # print "-".join(all[:2]), "-".join(all[2:])
        print all[:2], "or", all[2:]
    main()
