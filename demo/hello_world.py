#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/5/1 12:00
"""

import mornado.web
import mornado.httpserver
from mornado.options import define, options


define("port", default=8888, help="run on the given port", type=int)


class MainHandler(mornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

def main():
    print options.port
    application = mornado.web.Application(
        (r'/', MainHandler)
    )

    http_server = mornado.httpserver.HTTPServer(application)

    http_server.listen(options.port)


if __name__ == '__main__':
    main()