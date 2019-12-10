#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/12/9 16:54
"""

import socket
import select


HOST, PORT = "", 8888

def serve():
    sock = socket.socket()
    sock.bind((HOST, PORT))
    sock.setblocking(False)
    sock.listen(1)

    inputs = [sock, ]

    while True:
        r_list, w_list, e_list = select.select(inputs, [], [], 1)
        for event in r_list:
            if event == sock:
                print "client is connected"
                new_sock, addr = event.accept()
                inputs.append(new_sock)
            else:
                data = event.recv(1024)
                if data:
                    print "get client msg: %s" % data
                    event.send(b'\x31')
                else:
                    print "client disconnected"
                    inputs.remove(event)

if __name__ == '__main__':
    serve()

