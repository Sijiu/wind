# -*- coding:utf-8 -*-

import socket

HOST, PORT = "", 8002

listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

listen_socket.bind((HOST, PORT))

listen_socket.listen(1)
print "Serving HTTP on port %s" % PORT

while True:
    client_conn, client_address = listen_socket.accept()
    request = client_conn.recv(1024)
    print "request--", request

    http_response = """
HTTP/1.1 200 OK

Hello, Wind
"""
    client_conn.sendall(http_response)
    client_conn.close()