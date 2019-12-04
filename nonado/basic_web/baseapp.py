#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/12/2 11:48
"""
import json


def app(environ, start_response):
    """ A backbones WSGI application 这是WSGI 应用的主要部分

    This is a starting point for your own Web framework :)
    :param environ:
    :param start_response:
    :return:
    """
    status = "200 OK"
    response_headers = [("Content-Type", "text/plain")]
    print "environ %s" % environ
    # path = environ["PATH_INFO"]
    if "?" in environ["PATH_INFO"]:
        path, param = environ["PATH_INFO"].split("?")
    else:
        path, param = environ["PATH_INFO"], environ["QUERY_STRING"]
    tmp, tmp_str = {}, ""
    for p in param.split("&"):
        k, v = p.split("=") if "=" in p else "QUERY_STRING", None
        tmp_str += "%s: %s\n" % (k, v)
        tmp[k]=v
    param = json.dumps(param)
    param = tmp_str
    if path == "/index":
        start_response(status, response_headers)
        return {"Index %s \n" % param}
    elif path == "/home":
        start_response("996 ICU", response_headers)
        return {"Welcome HomePage %s \n" % param}
    else:
        start_response(status, response_headers)
        return {"Hello webServer from a simple WSGI application\n %s " % param}