#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/11/27 17:41
"""

class IOStream(object):

    def __init__(self):
        pass

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