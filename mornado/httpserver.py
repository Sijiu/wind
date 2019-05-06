#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/5/1 16:29
"""
import errno
import logging
import os
import socket

from mornado import ioloop, iostream, httputil

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

    def __init__(self, request_callback, io_loop=None, ssl_options=None):
        self.ssl_options = ssl_options
        self.request_callback = request_callback
        self.io_loop = io_loop
        self._socket = None
        self._started = False

    def listen(self, port, address=""):
        self.bind(port, address)
        self.start(1)

    def bind(self, port, address=""):
        assert not self._socket
        # 上边等价于如下 not not
        # if not not self._socket:  # if self._socket
        #     raise AssertionError
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        flags = fcntl.fcntl(self._socket.fileno(), fcntl.F_GETFD)
        flags |= fcntl.FD_CLOEXEC
        fcntl.fcntl(self._socket.fileno(), fcntl.F_SETFD, flags)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.setblocking(0)
        self._socket.bind((address, port))
        self._socket.listen(128)

    def start(self, num_processes=1):
        assert not self._started
        self._started = True
        if num_processes is None or num_processes <= 0:
            try:
                num_processes = os.sysconf("SC_NPROCESSORS_CONF")
            except ValueError:
                logging.error("Could not get num processors from sysconf;"
                              "running with one process")
                num_processes = 1
        if num_processes > 1 and ioloop.IOLoop.initialized():
            logging.error("Cannot run multiple processes: IOLoop instance")
            num_processes = 1
        if num_processes > 1:
            logging.info("Pre-forking %d server processes", num_processes)
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

    def _handle_events(self, fd, events):
        while True:
            try:
                conn, address = self._socket.accept()
            except socket.error, e:
                if e[0] in (errno.EWOULDBLOCK, errno.EAGAIN):
                    return
                raise
            if self.ssl_options is not None:
                assert ssl, "Python 2.6+ and OpenSSL required for SSL"
                conn = ssl.wrap_socket(conn, server_side=True, **self.ssl_options)
            try:
                stream = iostream.IOStream(conn, io_loop=self.io_loop)
                HTTPConnection(stream, address, self.request_callback, )
                # self.no_keep_alive, self.xheaders)
            except:
                logging.error("Error in connection callback", exc_info=True)


class HTTPConnection(object):
    def __init__(self, stream, address, request_callback):
        self.stream = stream
        self.address = address
        self.request_callback = request_callback
        self._request = None
        self._request_finished = False
        # self.stream.read_until("\r\n\r\n", self._on_headers)

    # def _on_headers(self, data):
    #     eol = data.find("\r\n")
    #     start_line = data[:eol]
    #     method, uri, version = start_line.split(" ")
    #     if not version.startswith("HTTP/"):
    #         raise Exception("Malformed HTTP version in HTTP Request-Line")
    #     headers = httputil.HTTPHeaders.parse(data[eol:])
    #     self._request = HTTPRequest(
    #         connection=self, method=method, uri=uri, version=version,
    #         headers=headers, remote_ip=self.address[0])
    #
    #     content_length = headers.get("Content-Length")
    #     if content_length:
    #         content_length = int(content_length)
    #         if content_length > self.stream.max_buffer_size:
    #             raise Exception("Content-Length too long")
    #         if headers.get("Expect") == "100-continue":
    #             self.stream.write("HTTP/1.1 100 (Continue)\r\n\r\n")
    #         self.stream.read_bytes(content_length, self._on_request_body)
    #         return
    #
    #     self.request_callback(self._request)
