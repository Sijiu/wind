#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/11/27 17:41
"""

class IOStream(object):
    """一个读写的非阻塞公共类

     支持三个方法: write(), read_until() 和 read_bytes()
     由于读写都是非阻塞和异步的, 所有的方法都会回调(翻译准确度待考)
     read_until() 读取套接字知道给定的分隔符
     read_bytes() 读取给定字节的套接字
        read_until() reads the socket until a given delimiter, and read_bytes() reads until a specified number
        of bytes have been read from the socket.
     """

    def __init__(self, socket, io_loop=None, max_buffer_size=104857600, read_chunk_size=4006):
        self.read_callback = None
        self._read_delimiter = None
        self._read_buffer = ""
        self._write_buffer = ""
        self._read_bytes = None
        self._read_callback = None
        self._write_callback = None
        self.socket = socket
        self.socket.setblocking(False)

        self.io_loop = io_loop or io_loop.IOLoop.instance()
        self._state = self.io_loop.ERROR

    def write(self, data, callback=None):
        """
        将传递的数据写到这个流中

        如果给了回调函数, 会将所有的数据字节成功写到流中, 如果有提前写入的数据和旧的写入回调函数, 新的回调函数将会覆盖旧的
        :param data:
        :param callback:
        :return:
        """
        self._check_closed()
        self._write_buffer += data
        self._add_io_state(self.io_loop.WRITE)
        self._write_callback = callback

    def read_until(self, delimiter, callback):
        """当给定分割符的时候调用回调"""
        assert not self._read_callback, "Already reading"
        loc = self._read_buffer.find(delimiter)
        if loc != -1:
            self._run_callback(callback, self._consume(loc + len(delimiter)))
            return
        self._check_closed()
        self.read_callback = callback
        self._read_delimiter = delimiter
        self._add_io_state(self.io_loop.READ)

    def read_bytes(self, num_bytes, callback):
        """当给定确定字节数的时候调用回调"""
        assert not self._read_callback, "Already reading"
        if len(self._read_buffer) >= num_bytes:
            callback(self._consume(num_bytes))
            return
        self._check_closed()
        self._read_bytes = num_bytes
        self._read_callback = callback
        self._add_io_state(self.io_loop.READ)

    def _check_closed(self):
        if not self.socket:
            raise IOError("Stream is closed")

    def _add_io_state(self, state):
        if not self._state & state:
            self._state = self._state | state
            self.io_loop.update_handler(self.socket.fileno(), self._state)