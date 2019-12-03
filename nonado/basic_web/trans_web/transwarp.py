#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/12/3 11:53
"""

# 全局ThreadLocal对象
import threading

ctx = threading.local()


# HTTP错误类
class HttpError(Exception):
    pass


# Request对象
class Request(object):

    def get(self, key, default=None):
        """

        :param key:
        :param default:
        :return: value
        """
        pass

    def input(self):
        """

        :return: dict
        """
        pass

    @property
    def path_info(self):
        pass

    @property
    def headers(self):
        """返回HTTPHeaders"""
        pass

    def cookie(self, name, default=None):
        """

        :return: name -> value
        """
        pass

class Response(object):

    def set_headers(self, key, value):
        pass

    def set_cookie(self, name, value, max_age=None, expires=None, path="/"):
        pass

    @property
    def status(self):
        pass

    @status.setter
    def status(self, value):
        pass


def get(path):
    pass


def view(path):
    pass


def post(path):
    pass

# 定义拦截器
def interceptor(pattern):
    pass


class TemplateEngine(object):

    def __call__(self, *args, **kwargs):
        pass


class Jinja2TemplateEngine(TemplateEngine):
    def __init__(self, template_dir, **kwargs):
        from jinja2 import Environment, FileSystemLoader
        self._env = Environment(loader=FileSystemLoader(template_dir), **kwargs)

    def __call__(self, path, model):
        return self._env.get_template(path).render(**model)


class WSGIApplication(object):
    def __init__(self, document_root=None, **kwargs):
        pass

    def add_url(self, func):
        pass

    def add_interceptor(self, func):
        pass

    @property
    def template_engine(self):
        pass

    def get_wsgi_application(self):
        def wsgi(env, start_response):
            pass
        return wsgi

    def run(self, port=4000, host=""):
        """开发模式会直接启动服务器

        :param port:
        :param host:
        :return:
        """
        from wsgiref.simple_server import make_server
        server = make_server(host, port, self.get_wsgi_application())
        server.serve_forever()


wsgi = WSGIApplication()


if __name__ == '__main__':
    wsgi.run()
else:
    application = wsgi.get_wsgi_application()