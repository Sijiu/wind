#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/11/29 9:31
"""
import socket
import sys
import os


print "pid=%s, pid=%s" % (os.getpid(), os.getpid())
_in, out, err = sys.stdin, sys.stdout, sys.stderr
print "stdin no=%s out_no=%s, err_no=%s" % (_in.fileno(), out.fileno(), err.fileno())

res = os.write(sys.stdout.fileno(), b"hello\n")
res1 = os.write(1, b"hello\n")
print "write standard %s" % res1

sock= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socks= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print "show fileno%s -- %s " % (sock.fileno(), socks.fileno())