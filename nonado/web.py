#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/11/27 16:21
"""
import httplib
import logging
import re


class RequestHandler(object):
    """
    本类的子类 应该定义一个有 get() 或者post() 方法的handler.

    如果想支持更多的方法, 可以在自己的 RequestHandler 类中重写 SUPPORTED_METHODS 类变量
    """

    supported_methods= ("GET", "HEAD", "POST", "DELETE", "PUT")

    def __init__(self, application, request, transforms=None):
        self.application = application
        self.request = request
        self._headers_written = False
        self._finished = False
        self._auto_finish = True
        self._transforms = transforms or []
        # self.ui = _O(("..."))
        # self.ui["modules"] = _O(("..."))
        self.clear()
        # 检查 WSGI 初始 connection 是否可用 Web服务器网关接口（Python Web Server Gateway Interface，缩写为WSGI）
        if hasattr(self.request, "connection"):
            self.request.connection.stream.set_close_callback(self.on_connection_close)

        def get(self, *args, **kwargs):
            raise HTTPError(405)


class Application(object):
    """
    组成web应用程序的请求处理程序的集合。

    此类的可调用实例可以直接传递给HTTPServer
    application = web.Application([
            (r"/", MainPageHandler),
        ])
        http_server = httpserver.HTTPServer(application)
        http_server.listen(8080)
        ioloop.IOLoop.instance().start()
    """

    def __init__(self, handlers=None, default_host="", transforms=None, wsgi=False, **settings):
        if transforms is None:
            self.transforms = []
            if settings.get("gzip"):
                pass
                # TODO
                # self.transforms.append(GZipContentEncoding)
            self.transforms.append(ChunkedTransferEncoding)
        else:
            self.transforms = transforms
        self.handlers = []
        self.named_handlers = {}
        self.default_host = default_host
        self.settings = settings
        self.ui_modules = {}
        self.ui_methods = {}
        self._wsgi = wsgi
        # self._load_ui_modules(settings.get("ui_modules", {}))
        # self._load_ui_methods(settings.get("ui_methods", {}))
        if self.settings.get("static_path"):
            print "setting static_path"
        if handlers: self.add_handlers(".*$", handlers)
        if self.settings.get("debug") and not wsgi:
            import autoreload
            autoreload.start()

    def add_handlers(self, host_pattern, host_handlers):
        """将给定的handlers 添加到 handler 列表"""
        if not host_pattern.endswith("$"):
            host_pattern += "$"
        handlers = []
        """
        具有通配符主机模式的处理程序是一个特殊的例子, 它们被添加到构造函数中，但是应该有更低优先级高于稍后添加的更精确的处理程序。
        如果存在通配符处理程序组，则应该总是最后一个在列表中，在其前面插入新组。
        The handlers with the wildcard host_pattern are a special
        case - they're added in the constructor but should have lower
        precedence than the more-precise handlers added later.
        If a wildcard handler group exists, it should always be last
        in the list, so insert new groups just before it.
        """
        if self.handlers and self.handlers[-1][0].pattern == ".*$":
            self.handlers.insert(-1, (re.compile(host_pattern), handlers))
        else:
            self.handlers.append((re.compile(host_pattern), handlers))

        for spec in host_handlers:
            if type(spec) is type(()):
                assert len(spec) in (2,3)
                pattern = spec[0]
                handler = spec[1]
                if len(spec) == 3:
                    kwargs = spec[2]
                else:
                    kwargs = {}
                spec = URLSpec(pattern, handler, kwargs)
            handlers.append(spec)
            if spec.name:
                if spec.name in self.named_handlers:
                    logging.warning("Multiple handlers named %s; replacing previous value", spec.name)
                self.named_handlers[spec.name] = spec



class OutputTransform(object):
    """A transform modifies the result of an HTTP request (e.g., GZip encoding)

    A new transform instance is created for every request. See the
    ChunkedTransferEncoding example below if you want to implement a
    new Transform.
    """
    def __init__(self, request):
        pass

    def transform_first_chunk(self, headers, chunk, finishing):
        return headers, chunk

    def transform_chunk(self, chunk, finishing):
        return chunk


class GZipContentEncoding(OutputTransform):
    """将gzip内容编码应用于响应
    """

    CONTENT_TYPES = set([
        "text/plain", "text/html", "text/css", "text/xml",
        "application/x-javascript", "application/xml", "application/atom+xml",
        "text/javascript", "application/json", "application/xhtml+xml"])
    MIN_LENGTH = 5

    def __init__(self, request):
        self._gzipping = request.supports_http_1_1() and \
                         "gzip" in request.headers.get("Accept-Encoding", "")


class ChunkedTransferEncoding(OutputTransform):
    """将分块传输编码应用于响应
    """
    def __init__(self, request):
        self._chunking = request.supports_http_1_1()


class HTTPError(Exception):
    """An exception that will turn into an HTTP error response."""
    def __init__(self, status_code, log_message=None, *args):
        self.status_code = status_code
        self.log_message = log_message
        self.args = args

    def __str__(self):
        message = "HTTP %d: %s" % (
            self.status_code, httplib.responses[self.status_code])
        if self.log_message:
            return message + " (" + (self.log_message % self.args) + ")"
        else:
            return message


class URLSpec(object):
    """Specifies mappings between URLs and handlers."""
    def __init__(self, pattern, handler_class, kwargs={}, name=None):
        """Creates a URLSpec.

        Parameters:
        pattern: Regular expression to be matched.  Any groups in the regex
            will be passed in to the handler's get/post/etc methods as
            arguments.
        handler_class: RequestHandler subclass to be invoked.
        kwargs (optional): A dictionary of additional arguments to be passed
            to the handler's constructor.
        name (optional): A name for this handler.  Used by
            Application.reverse_url.
        """
        if not pattern.endswith('$'):
            pattern += '$'
        self.regex = re.compile(pattern)
        self.handler_class = handler_class
        self.kwargs = kwargs
        self.name = name
        self._path, self._group_count = self._find_groups()

    def _find_groups(self):
        """Returns a tuple (reverse string, group count) for a url.

        For example: Given the url pattern /([0-9]{4})/([a-z-]+)/, this method
        would return ('/%s/%s/', 2).
        """
        pattern = self.regex.pattern
        if pattern.startswith('^'):
            pattern = pattern[1:]
        if pattern.endswith('$'):
            pattern = pattern[:-1]

        if self.regex.groups != pattern.count('('):
            # The pattern is too complicated for our simplistic matching,
            # so we can't support reversing it.
            return None, None

        pieces = []
        for fragment in pattern.split('('):
            if ')' in fragment:
                paren_loc = fragment.index(')')
                if paren_loc >= 0:
                    pieces.append('%s' + fragment[paren_loc + 1:])
            else:
                pieces.append(fragment)

        return ''.join(pieces), self.regex.groups

    def reverse(self, *args):
        assert self._path is not None, \
            "Cannot reverse url regex " + self.regex.pattern
        assert len(args) == self._group_count, "required number of arguments "\
            "not found"
        if not len(args):
            return self._path
        return self._path % tuple([str(a) for a in args])

url = URLSpec