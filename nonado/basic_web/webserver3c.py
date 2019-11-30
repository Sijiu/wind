#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/11/29 16:36
"""

import os
import signal
import socket
import time


SERVER_ADDRESS = (HOST, PORT) = '', 8889
REQUEST_QUEUE_SIZE = 5


def handle_request(client_connection):
    request = client_connection.recv(1024)
    print 'Child PID: %s, Parent PId %s' % (os.getpid(), os.getppid())
    print (request.decode())
    http_response = b"""
    HTTP/1.1 200 OK
    
    Hello Client!
    """
    client_connection.sendall(http_response)
    time.sleep(5)


def server_forever():
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_socket.bind(SERVER_ADDRESS)
    listen_socket.listen(REQUEST_QUEUE_SIZE)

    print "ServerHTTP on port %s" % PORT
    print "Parent PID(PPID): %s \n" % os.getpid()

    # signal.signal(signal.SIGCHLD, grim_reaper)

    clients = []
    while True:
        client_connection, client_address = listen_socket.accept()
        # store the reference otherwise it's garbage collected
        # on the next loop run
        # clients.append(client_connection)
        pid = os.fork()
        if pid ==0: # child
            listen_socket.close() # close child copy
            handle_request(client_connection)
            client_connection.close()
            os._exit(0)  # child exit here
        else:
            client_connection.close() # 关闭父进程复制,及终止循环
            print len(clients)


def grim_reaper(signum, frame):
    pid, status = os.wait()
    print "Child ------pid %s terminated with status %s " % (pid, status)


if __name__ == '__main__':
    server_forever()
