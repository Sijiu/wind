#!/usr/bin/env python
#
# Copyright 2009 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import tornado_cut.httpserver
import tornado_cut.ioloop
import tornado_cut.options
import tornado_cut.web

from tornado_cut.options import define, options

define("port", default=8888, help="run on the given port", type=int)


class MainHandler(tornado_cut.web.RequestHandler):
    def get(self):
        self.write("Tor_cut")


class IndexHandler(tornado_cut.web.RequestHandler):
    def get(self):
        self.write("Index Page-_-_-")

def main():
    tornado_cut.options.parse_command_line()
    application = tornado_cut.web.Application([
        (r"/", MainHandler),
        (r"/index", IndexHandler),
    ])
    http_server = tornado_cut.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado_cut.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
