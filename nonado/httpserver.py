#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/11/27 16:43
"""
import errno
import logging
import os
import socket

from nonado import ioloop, iostream

try:
    import fcntl
except ImportError:
    if os.name == 'nt':
        import win32_support as fcntl
    else:
        raise

try:
    import ssl  # Python 2.6+
except ImportError:
    ssl = None


class HTTPServer(object):

    def __init__(self, request_callback, no_keep_alive=False, io_loop=None, xheaders=False, ssl_options=None):
        """
        用请求的毁掉函数初始化服务
        如果你用 pre-forking/start() 来替代 listen() 方法启动你的服务, 你不用传递IOLoop接口 到改构造器
        在forking进程之后 每一个提前fork的子进程会创建他们自己的IOLoop接口
        :param request_callback:
        :param no_keep_alive:
        :param io_loop:
        :param xheaders:
        :param ssl_options:
        """
        self.request_callback = request_callback
        self.no_keep_alive = no_keep_alive
        self.io_loop = io_loop
        self.xheaders = xheaders
        self.ssl_options = ssl_options
        self._socket = None
        self._started = False

    def listen(self, port, address=""):
        """在一个进程中绑定给定port 并启动服务 """
        self.bind(port, address)
        self.start(1)

    def bind(self, port, address=""):
        """
        绑定服务到给定的端口和Ip地址上
        启动服务调用 start(), 如果你想用单进程运行服务, 你可以调用 listen()
        :param port:
        :param address:
        :return:
        """
        assert not self._socket
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        flags = fcntl.fcntl(self._socket.fileno(), fcntl.F_GETFD)
        flags |= fcntl.FD_CLOEXEC
        fcntl.fcntl(self._socket.fileno(), fcntl.F_SETFD, flags)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.setblocking(0)
        self._socket.bind((address, port))
        self._socket.listen(128)

    def start(self, num_processes=1):
        """
        如果 num_processes >1 将会创建确定数量的进程
        :param num_processes:
        :return:
        """
        assert not self._started
        self._started = True
        if num_processes is None or num_processes <= 0:
            # 使用 sysconf 检查CPU核数
            try:
                num_processes = os.sysconf("SC_NPROCESSORS_CONF")
            except ValueError:
                logging.error("不能通过sysconf获取到 CPU核数,将以但进程运行.")
                num_processes = 1
        if num_processes > 1 and ioloop.IOLoop.initialized():
            logging.error("")
            num_processes = 1
        if num_processes > 1:
            logging.info("Pre-forking %s server process", num_processes)
            for i in range(num_processes):
                if os.fork() == 0:
                    self.io_loop = ioloop.IOLoop.instance()
                    self.io_loop.add_handler(
                        self._socket.fileno(), self._handle_events, ioloop.IOLoop.READ
                    )
                    return
            os.waitpid(-1, 0)
        else:
            if not self.io_loop:
                self.io_loop = ioloop.IOLoop.instance()
            self.io_loop.add_handler(self._socket.fileno(), self._handle_events, ioloop.IOLoop.READ)

    def stop(self):
        self.io_loop.remove_handeler(self._socket.fileno())

    def _handle_events(self, fd, events):
        while True:
            try:
                connection, address = self._socket.accept()
            except socket.error, e:
                if e[0] in (errno.EWOULDBLOCK, errno.EAGAIN):
                    return
                raise
            if self.ssl_options is not None:
                assert ssl, "Python 2.6+ and OpenSSL required for SSL"
                connection = ssl.wrap_socket(
                    connection, server_side=True, **self.ssl_options)
            try:
                stream = iostream.IOStream(connection, io_loop=self.io_loop)
                HTTPConnection(stream, address, self.request_callback,
                               self.no_keep_alive, self.xheaders)
            except:
                logging.error("Error in connection callback", exc_info=True)


class HTTPConnection(object):
    """处理一个连接到 HTTP客户端, 处理HTTP请求

    解析HTTP头和body, 并且处理请求回调函数, 知道HTTP连接被关闭.
    """

    def __init__(self, stream, address, request_callback, no_keep_alive=False, xheaders=False):
        self.stream = stream
        self.address = address
        self.request_callback = request_callback
        self.no_keep_alive = no_keep_alive
        self.xheaders = xheaders
        self._request = None
        self._request_finished = False
        self.stream.read_until("\r\n\r\n", self._on_headers)

    def write(self, chunk):
        assert self._request, "Request closed"
        if not self.stream.closed():
            self.stream.write(chunk, self._on_write_complete)

    def finish(self):
        assert self._request, "Request closed"
        self._request_finished = True
        if not self.stream.writing():
            self._finish_request()

    def _on_write_complete(self):
        if self._request_finished:
            self._finish_request()

    def _finish_request(self):
        if self.no_keep_alive:
            disconnect = True
        else:
            connection_header = self._request.headers.get("Connection")
            if self._request.supports_http_1_1():
                disconnect = connection_header == "close"
            elif ("Content-Length" in self._request.headers
                  or self._request.method in ("HEAD", "GET")):
                disconnect = connection_header != "Keep-Alive"
            else:
                disconnect = True
        self._request = None
        self._request_finished = False
        if disconnect:
            self.stream.close()
            return
        self.stream.read_until("\r\n\r\n", self._on_headers)