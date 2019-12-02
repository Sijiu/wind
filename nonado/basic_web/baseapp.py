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
    if "?" in environ["PATH_INFO"]:
        path, param = environ["PATH_INFO"].split("?")
    else:
        path, param = environ["PATH_INFO"], environ["QUERY_STRING"]
    tmp, tmp_str = {}, ""
    for p in param.split("&"):
        k, v = p.split("=")
        tmp_str += "%s_%s#"
        tmp[k]=v
    param = json.dumps(tmp)
    param = tmp_str
    if path == "/index":
        start_response(status, response_headers)
        return {"Index \n" % param}
    elif path == "/home":
        start_response("404, None", response_headers)
        return {"Welcome HomePage % \n" % param}
    else:
        start_response(status, response_headers)
        return {"Hello webServer from a simple WSGI application\n %s " % param}