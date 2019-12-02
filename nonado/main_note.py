#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/11/28 9:29
nonado 即11月 tornado源码模拟说明
"""
import inspect


def timeit(func):
    def run(*argv):
       print func.__name__, func.__class__.__name__
       if argv:
            ret = func(*argv)
       else:
            ret = func()
       return ret
    return run


class MyClass:

    @timeit
    def function_one(self):
        print "%s.%s invoked"%(self.__class__.__name__, self.get_current_function_name())

    def get_current_function_name(self):
        return inspect.stack()[1][3]


@timeit
def t(a):
    print a


class Note(MyClass):

    def __init__(self):
        self.note = "这是一段说明tornado1.1.0版本用到主要类及方法的个人理解说明文档, 本类中的每一个方法名, 即tornado包中的一个模块名(文件名)"

    @timeit
    def web(self):
        self.note += "\n web.py -> RequestHandler "
        self.note += "\n        -> RequestHandler "

    def httpserver(self):
        self.note += "\n HttpServer. _handle_events   -> iostream.IOStream "

        self.note += "\n HttpConnection. _on_headers -> httputil.HTTPHeaders "

    def iostream(self):
        self.note += "\n"

    def httputil(self):
        self.note += "\n"

    def think(self):
        think = """
        还是没有搞懂这个问题, 现在的环境总是在
        ERROR:root:Exception in I/O handler for fd 1412
        Traceback (most recent call last):
          File "E:\docs\wind\nonado\ioloop.py", line 252, in start
            self._handlers[fd](fd, events)
        KeyError: 1412L
        
        需要研究这个问题是怎么产生的, 并且从另一个角度研究一下 一个平常的web服务器怎么开发
        https://linux.cn/article-6817-1.html
        https://ruslanspivak.com/lsbaws-part1/
        """
        print think


class MiddleWare(object):
    """ 这个地方帮助解决了 tornado 运行在 web server 上的问题,
    https://www.v2ex.com/t/283059

    有一个 V 站的自制服务器, 值得研究一下 https://jolla.readthedocs.io/zh/latest/
    其实一个 wsgi server 的重要之处就在于用environ去跑 web app 得到返回结果这一步，
    这一步和前面的 application 实现相辅相成，然后框架和服务器都根据这套标准，大家就可以愉快的一起工作了。
    """

    def __init__(self):
        print "middleware"
        """ 中间件可以提前拦截一些东西, 通过请求中的字符戳, 比如反扒, IP 过滤等等
        """


class WSGIRef(object):

    def __init__(self):
        print "https://www.liaoxuefeng.com/wiki/897692888725344/923057027806560"

if __name__ == '__main__':
    note = Note()
    note.web()
