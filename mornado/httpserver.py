#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/5/1 16:29
"""
import logging
import os
import socket

from mornado import ioloop

try:
    import fcntl
except ImportError:
    if os.name == 'nt':
        import win32_support as fcntl
    else:
        raise

class HTTPServer(object):

    def __init__(self, request_callback, io_loop=None):
        self.request_callback  =request_callback
        self.io_loop = io_loop

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
        if num_processes >1 and ioloop.IOLoop.initialized():
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
