#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/11/29 9:11
"""


import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 6666))

sock.sendall(b'Hi web_demo')
data = sock.recv(1024)
print data.decode()