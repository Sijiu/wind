#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/12/3 15:32
"""


from transwarp import get, view
import os
from transwarp import WSGIApplication,Jinja2TemplateEngine
import urls

# @view('index.html')
# @get("/")
# def test_index():
#     return dict(name="airport", socore=9.7, time="20191203")


wsgi = WSGIApplication(os.path.dirname(os.path.abspath(__file__)))

template_engine = Jinja2TemplateEngine(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))
wsgi.template_engine = template_engine
wsgi.add_module(urls)

if __name__ == '__main__':
    wsgi.run()
    print "why error with liao'xue'feng's framework"
