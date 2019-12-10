#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/12/9 16:32
"""

import socket
import select

HOST, PORT = "", 8888



def client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 不经过WAIT_TIME，直接关闭
    sock.setblocking(False)
    try:
        sock.connect((HOST, PORT))
    except Exception, e:
        print e

    r_inputs, w_inputs, e_inputs = set(), set(), set()
    r_inputs.add(sock)
    w_inputs.add(sock)
    e_inputs.add(sock)

    while True:
        try:
            r_list, w_list, e_list = select.select(r_inputs, w_inputs, e_inputs, 1)
            print "r======"
            for event in r_list:
                try:
                    data = event.recv(1024)
                except Exception, e:
                    print e
                if data:
                    print "data %s" % data
                    print "received Msg =="
                else:
                    print "disconnected"
                    r_inputs.clear()
            print "w-------", w_list
            if w_list:
                w_inputs.clear()
            print "e--------"
            if e_inputs:
                e_inputs.clear()
        except OSError, e:
            print e

if __name__ == '__main__':
    client()